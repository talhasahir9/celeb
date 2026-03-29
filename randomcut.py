import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import random
import threading
import subprocess
import concurrent.futures
import time
import re
import queue  # <-- Naya Thread-Safe System
from imageio_ffmpeg import get_ffmpeg_exe

# --- GOOGLE DRIVE IMPORTS ---
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
# ----------------------------

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class RandomClipExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Super Fast Random Clipper (Multi-Thread Safe)")
        self.geometry("750x750")

        self.video_paths = []
        self.output_folder = ""
        self.drive_service = None 
        
        self.is_running = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()

        # --- NEW: Thread-Safe Systems ---
        self.ui_queue = queue.Queue()  # UI updates ke liye line
        self.upload_lock = threading.Lock()  # Drive API ko crash hone se bachanay ke liye
        
        # --- UI ELEMENTS ---
        self.label_title = ctk.CTkLabel(self, text="🎬 Instant Random Clip Maker", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=10)

        # 1. Video Selection
        self.btn_video = ctk.CTkButton(self, text="📂 Select Multiple Videos", command=self.select_videos)
        self.btn_video.pack(pady=5)
        self.lbl_video = ctk.CTkLabel(self, text="0 videos selected", text_color="gray")
        self.lbl_video.pack()

        # 2. Output Folder Selection
        self.btn_output = ctk.CTkButton(self, text="📁 Select Output Folder", command=self.select_output)
        self.btn_output.pack(pady=5)
        self.lbl_output = ctk.CTkLabel(self, text="No folder selected", text_color="gray")
        self.lbl_output.pack()

        # 3. Settings
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=10, padx=40, fill="x")

        self.lbl_clips = ctk.CTkLabel(self.frame_settings, text="Clips per video:")
        self.lbl_clips.grid(row=0, column=0, padx=20, pady=10)
        self.entry_clips = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_clips.insert(0, "10") 
        self.entry_clips.grid(row=0, column=1, padx=20, pady=10)

        self.lbl_duration = ctk.CTkLabel(self.frame_settings, text="Clip Duration (sec):")
        self.lbl_duration.grid(row=1, column=0, padx=20, pady=10)
        self.entry_duration = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_duration.insert(0, "10.0") 
        self.entry_duration.grid(row=1, column=1, padx=20, pady=10)

        self.lbl_threads = ctk.CTkLabel(self.frame_settings, text="Max Threads (Speed):")
        self.lbl_threads.grid(row=2, column=0, padx=20, pady=10)
        self.entry_threads = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_threads.insert(0, "3") # Ab aap 5 ya 10 bhi rakhein toh crash nahi hoga!
        self.entry_threads.grid(row=2, column=1, padx=20, pady=10)

        self.lbl_drive_folder = ctk.CTkLabel(self.frame_settings, text="Drive Folder ID:")
        self.lbl_drive_folder.grid(row=3, column=0, padx=20, pady=10)
        self.entry_drive_folder = ctk.CTkEntry(self.frame_settings, width=180, placeholder_text="Paste Folder ID here...")
        self.entry_drive_folder.grid(row=3, column=1, padx=20, pady=10)

        # 4. Control Buttons
        self.frame_controls = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controls.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.frame_controls, text="🚀 Start Batch", fg_color="green", hover_color="darkgreen", command=self.start_processing_thread)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_pause = ctk.CTkButton(self.frame_controls, text="⏸️ Pause", fg_color="orange", hover_color="darkorange", state="disabled", command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=10)

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="🛑 Stop", fg_color="red", hover_color="darkred", state="disabled", command=self.stop_processing)
        self.btn_stop.grid(row=0, column=2, padx=10)

        # 5. Progress Bar & Live Status
        self.progress_bar = ctk.CTkProgressBar(self, width=600)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(self, text="Status: Ready", text_color="yellow", font=ctk.CTkFont(size=14))
        self.lbl_status.pack(pady=5)

        # 6. Live Logs Screen
        self.log_box = ctk.CTkTextbox(self, width=650, height=200, state="disabled", fg_color="#1e1e1e", text_color="#00ff00", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(pady=10)

        # Start the Queue Processor (Yeh background mein hamesha chalta rahega)
        self.after(100, self.process_ui_queue)

    # --- NEW THREAD-SAFE UI UPDATES ---
    def process_ui_queue(self):
        # Jab tak line mein messages hain, unko screen par lagata jaye
        while not self.ui_queue.empty():
            try:
                msg_type, data = self.ui_queue.get_nowait()
                if msg_type == "log":
                    self.log_box.configure(state="normal")
                    self.log_box.insert(ctk.END, data + "\n")
                    self.log_box.see(ctk.END)
                    self.log_box.configure(state="disabled")
                elif msg_type == "status":
                    self.lbl_status.configure(text=data)
                elif msg_type == "progress":
                    self.progress_bar.set(data)
            except queue.Empty:
                break
        
        # Har 100 millisecond baad dubara check karega
        self.after(100, self.process_ui_queue)

    def log(self, text):
        self.ui_queue.put(("log", text))

    def update_progress(self, value):
        self.ui_queue.put(("progress", value))

    def update_status(self, text):
        self.ui_queue.put(("status", text))

    # --- BUTTON COMMANDS ---
    def select_videos(self):
        paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")])
        if paths:
            self.video_paths = list(paths)
            self.lbl_video.configure(text=f"{len(self.video_paths)} videos selected")

    def select_output(self):
        self.output_folder = filedialog.askdirectory()
        if self.output_folder:
            self.lbl_output.configure(text=self.output_folder)

    def toggle_pause(self):
        if self.is_paused:
            self.pause_event.set()
            self.is_paused = False
            self.btn_pause.configure(text="⏸️ Pause")
            self.log("▶️ System Resumed")
        else:
            self.pause_event.clear()
            self.is_paused = True
            self.btn_pause.configure(text="▶️ Resume")
            self.log("⏸️ System Paused")

    def stop_processing(self):
        self.is_running = False
        self.pause_event.set() 
        self.btn_stop.configure(state="disabled")
        self.log("🛑 Stopping tasks... Please wait for ongoing cuts to finish.")

    # --- GOOGLE DRIVE ---
    def setup_google_drive(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try: creds.refresh(Request())
                except: pass
            if not creds or not creds.valid:
                if not os.path.exists('credentials.json'): return None
                try:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception: return None
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        try:
            return build('drive', 'v3', credentials=creds, cache_discovery=False)
        except Exception: return None

    # --- PROCESSING ---
    def start_processing_thread(self):
        if not self.video_paths or not self.output_folder:
            messagebox.showerror("Error", "Please select Videos and Output Folder!")
            return
        self.is_running = True
        self.is_paused = False
        self.pause_event.set()
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸️ Pause")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.init_drive_and_run).start()

    def init_drive_and_run(self):
        self.drive_service = self.setup_google_drive()
        if self.drive_service:
            self.log("✅ Google Drive Connected!")
        self.log("🚀 Multi-Thread Safe Processing Started!")
        self.run_batch_processing()

    def run_batch_processing(self):
        try: max_threads = int(self.entry_threads.get())
        except ValueError: max_threads = 3
        
        total_videos = len(self.video_paths)
        completed_videos = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(self.process_single_video, vid): vid for vid in self.video_paths}
            for future in concurrent.futures.as_completed(futures):
                if not self.is_running: break 
                completed_videos += 1
                self.update_progress(completed_videos / total_videos)
        
        self.is_running = False
        self.ui_queue.put(("log", "✅ All tasks finished!"))
        self.ui_queue.put(("status", "Status: Ready"))
        # Tkinter UI states update main thread se karne par safe hain
        self.after(0, lambda: self.btn_start.configure(state="normal"))
        self.after(0, lambda: self.btn_pause.configure(state="disabled"))
        self.after(0, lambda: self.btn_stop.configure(state="disabled"))

    # --- SAFE DURATION GETTER ---
    def get_video_duration(self, video_path, ffmpeg_exe):
        try:
            # Ghost Console Fix
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            command = [ffmpeg_exe, "-i", video_path]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore', startupinfo=startupinfo)
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            return 0
        except Exception:
            return 0

    # --- SINGLE VIDEO RANDOM CUTTER ---
    def process_single_video(self, video_path):
        try:
            num_clips = int(self.entry_clips.get())
            clip_duration = float(self.entry_duration.get())
            duration_int = int(clip_duration) 
            base_video_name = os.path.splitext(os.path.basename(video_path))[0]
            ffmpeg_exe = get_ffmpeg_exe()

            total_seconds = int(self.get_video_duration(video_path, ffmpeg_exe))

            if total_seconds <= 0:
                self.log(f"❌ Corrupt video or unreadable length: {base_video_name[:15]}")
                return

            start_margin = 30 if total_seconds > 100 else 0
            end_margin = 30 if total_seconds > 100 else 0

            if total_seconds <= (start_margin + end_margin + duration_int):
                self.log(f"⚠️ Video '{base_video_name[:15]}' is short. Using full length.")
                valid_range = list(range(0, max(1, total_seconds - duration_int)))
            else:
                valid_range = list(range(start_margin, total_seconds - end_margin - duration_int))

            if not valid_range:
                return

            try:
                selected_seconds = random.sample(valid_range, num_clips)
            except ValueError:
                selected_seconds = random.sample(valid_range, len(valid_range))

            self.log(f"🎬 Cutting {len(selected_seconds)} clips from: {base_video_name[:20]}...")

            for idx, sec in enumerate(selected_seconds):
                self.pause_event.wait()
                if not self.is_running: break
                
                self.update_status(f"Cutting Clip {idx+1}/{len(selected_seconds)} for '{base_video_name[:15]}...'")
                
                clip_number_str = f"{idx + 1:02d}"
                output_filename = os.path.join(self.output_folder, f"{clip_number_str} random {base_video_name}.mp4")
                
                # Ghost Console Fix for Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                command = [
                    ffmpeg_exe, "-y", "-ss", str(sec), "-i", video_path, 
                    "-t", str(clip_duration), "-c:v", "copy", "-c:a", "copy", output_filename
                ]
                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
                
                self.log(f"✂️ Saved '{clip_number_str} random clip' (from {sec}s)")

                # Google Drive Thread-Safe Upload
                if self.drive_service:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            folder_id = self.entry_drive_folder.get().strip()
                            file_metadata = {'name': os.path.basename(output_filename)}
                            if folder_id: file_metadata['parents'] = [folder_id]
                            media = MediaFileUpload(output_filename, mimetype='video/mp4', resumable=True)
                            
                            # Yahan Lock lagaya hai taa ke 2 videos ek sath upload maari toh API crash na ho!
                            with self.upload_lock:
                                uploaded_file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                            
                            self.log(f"✅ Uploaded to Drive: {uploaded_file.get('id')}")
                            break 
                        except Exception as upload_err:
                            if attempt < max_retries - 1:
                                time.sleep(3)
                            else:
                                self.log(f"❌ Upload Failed: {str(upload_err)}")

        except Exception as e:
            self.log(f"❌ Error in {video_path}: {str(e)}")

if __name__ == "__main__":
    app = RandomClipExtractorApp()
    app.mainloop()

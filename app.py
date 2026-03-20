import customtkinter as ctk
from tkinter import filedialog, messagebox
import cv2
from deepface import DeepFace
import os
import random
import threading
import subprocess
import concurrent.futures
from imageio_ffmpeg import get_ffmpeg_exe
import time
import gc

# --- GOOGLE DRIVE IMPORTS ---
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
# ----------------------------

# Modern Theme Setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Google Drive Access Scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class ClipExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Celeb Clip Extractor (Ultimate Batch Edition)")
        self.geometry("750x850")

        # Variables
        self.video_paths = []
        self.image_paths = []
        self.output_folder = ""
        self.drive_service = None 
        
        # Threading & Crash Prevention Controls
        self.is_running = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()
        
        # --- NAYA LOCK ---
        self.ai_lock = threading.Lock()

        # --- UI ELEMENTS ---
        self.label_title = ctk.CTkLabel(self, text="🎬 AI Celeb Clip Extractor (Pro)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=10)

        # 1. Video Selection
        self.btn_video = ctk.CTkButton(self, text="📂 Select Multiple Videos", command=self.select_videos)
        self.btn_video.pack(pady=5)
        self.lbl_video = ctk.CTkLabel(self, text="0 videos selected", text_color="gray")
        self.lbl_video.pack()

        # 2. Celeb Image Selection
        self.btn_image = ctk.CTkButton(self, text="🖼️ Select Celeb Image(s)", command=self.select_images)
        self.btn_image.pack(pady=5)
        self.lbl_image = ctk.CTkLabel(self, text="0 images selected", text_color="gray")
        self.lbl_image.pack()

        # 3. Output Folder Selection
        self.btn_output = ctk.CTkButton(self, text="📁 Select Output Folder", command=self.select_output)
        self.btn_output.pack(pady=5)
        self.lbl_output = ctk.CTkLabel(self, text="No folder selected", text_color="gray")
        self.lbl_output.pack()

        # 4. Settings
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=10, padx=40, fill="x")

        self.lbl_clips = ctk.CTkLabel(self.frame_settings, text="Clips per video:")
        self.lbl_clips.grid(row=0, column=0, padx=20, pady=10)
        self.entry_clips = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_clips.insert(0, "5")
        self.entry_clips.grid(row=0, column=1, padx=20, pady=10)

        self.lbl_duration = ctk.CTkLabel(self.frame_settings, text="Clip Duration (sec):")
        self.lbl_duration.grid(row=1, column=0, padx=20, pady=10)
        self.entry_duration = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_duration.insert(0, "5.0")
        self.entry_duration.grid(row=1, column=1, padx=20, pady=10)

        self.lbl_threads = ctk.CTkLabel(self.frame_settings, text="Max Threads (Simultaneous Videos):")
        self.lbl_threads.grid(row=2, column=0, padx=20, pady=10)
        self.entry_threads = ctk.CTkEntry(self.frame_settings, width=80)
        self.entry_threads.insert(0, "2")
        self.entry_threads.grid(row=2, column=1, padx=20, pady=10)

        # Drive Folder ID
        self.lbl_drive_folder = ctk.CTkLabel(self.frame_settings, text="Drive Folder ID (Optional):")
        self.lbl_drive_folder.grid(row=3, column=0, padx=20, pady=10)
        self.entry_drive_folder = ctk.CTkEntry(self.frame_settings, width=180, placeholder_text="Paste Folder ID here...")
        self.entry_drive_folder.grid(row=3, column=1, padx=20, pady=10)

        # 5. Control Buttons
        self.frame_controls = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controls.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.frame_controls, text="🚀 Start Batch", fg_color="green", hover_color="darkgreen", command=self.start_processing_thread)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_pause = ctk.CTkButton(self.frame_controls, text="⏸️ Pause", fg_color="orange", hover_color="darkorange", state="disabled", command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=10)

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="🛑 Stop", fg_color="red", hover_color="darkred", state="disabled", command=self.stop_processing)
        self.btn_stop.grid(row=0, column=2, padx=10)

        # 6. Progress Bar & Live Status
        self.progress_bar = ctk.CTkProgressBar(self, width=600)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(self, text="Status: Ready", text_color="yellow", font=ctk.CTkFont(size=14))
        self.lbl_status.pack(pady=5)

        # 7. Live Logs Screen
        self.log_box = ctk.CTkTextbox(self, width=650, height=200, state="disabled", fg_color="#1e1e1e", text_color="#00ff00", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(pady=10)

    # --- UI UPDATE & LOGGING FUNCTIONS ---
    def log(self, text):
        self.after(0, self._safe_log, text)

    def _safe_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert(ctk.END, text + "\n")
        self.log_box.see(ctk.END)
        self.log_box.configure(state="disabled")

    def update_progress(self, value):
        self.after(0, lambda: self.progress_bar.set(value))

    def update_status(self, text):
        self.after(0, lambda: self.lbl_status.configure(text=text))

    # --- BUTTON FUNCTIONS ---
    def select_videos(self):
        paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4 *.mkv *.avi")])
        if paths:
            self.video_paths = list(paths)
            self.lbl_video.configure(text=f"{len(self.video_paths)} videos selected")

    def select_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")])
        if paths:
            self.image_paths = list(paths)
            self.lbl_image.configure(text=f"{len(self.image_paths)} images selected")

    def select_output(self):
        self.output_folder = filedialog.askdirectory()
        if self.output_folder:
            self.lbl_output.configure(text=self.output_folder)

    def toggle_pause(self):
        if self.is_paused:
            self.pause_event.set()
            self.is_paused = False
            self.btn_pause.configure(text="⏸️ Pause")
            self.update_status("Status: Resumed...")
            self.log("▶️ System Resumed...")
        else:
            self.pause_event.clear()
            self.is_paused = True
            self.btn_pause.configure(text="▶️ Resume")
            self.update_status("Status: Paused...")
            self.log("⏸️ System Paused... (Threads waiting)")

    def stop_processing(self):
        self.is_running = False
        self.pause_event.set() 
        self.update_status("Status: Stopping... Please wait.")
        self.log("🛑 Stopping... (Waiting for current ongoing tasks to finish)")
        self.btn_stop.configure(state="disabled")

    # --- GOOGLE DRIVE SETUP FUNCTION ---
    def setup_google_drive(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    pass
            if not creds or not creds.valid:
                if not os.path.exists('credentials.json'):
                    self.log("⚠️ credentials.json not found! Google Drive upload skipped.")
                    return None
                try:
                    self.log("🔑 Opening browser for Google Drive Authentication...")
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.log(f"❌ Google Auth Error: {str(e)}")
                    return None
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        try:
            service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            return service
        except Exception as e:
            self.log(f"❌ Drive Service Error: {str(e)}")
            return None

    def start_processing_thread(self):
        if not self.video_paths or not self.image_paths or not self.output_folder:
            messagebox.showerror("Error", "Please select Videos, Celeb Image(s), and Output Folder!")
            return
        
        self.is_running = True
        self.is_paused = False
        self.pause_event.set()

        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸️ Pause")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        
        self.log("⏳ Connecting to Google Drive...")
        threading.Thread(target=self.init_drive_and_run).start()

    def init_drive_and_run(self):
        self.drive_service = self.setup_google_drive()
        if self.drive_service:
            self.log("✅ Google Drive Connected Successfully!")
        else:
            self.log("⚠️ Processing without Auto-Upload.")
            
        self.log("🚀 Batch Processing Started!")
        self.run_batch_processing()

    # --- CORE BATCH & MULTI-THREAD LOGIC ---
    def run_batch_processing(self):
        try:
            max_threads = int(self.entry_threads.get())
        except ValueError:
            max_threads = 2
            
        total_videos = len(self.video_paths)
        completed_videos = 0

        self.log(f"⚡ Starting with {max_threads} parallel threads...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(self.process_single_video, vid): vid for vid in self.video_paths}
            
            for future in concurrent.futures.as_completed(futures):
                if not self.is_running:
                    break 
                
                completed_videos += 1
                self.update_progress(completed_videos / total_videos)
        
        self.after(0, self.finish_processing)

    def finish_processing(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled")
        self.btn_stop.configure(state="disabled")
        self.update_status("Status: Ready")
        self.log("✅ All tasks finished or stopped.")

    # --- SINGLE VIDEO PROCESSING ---
    def process_single_video(self, video_path):
        cap = None
        try:
            num_clips = int(self.entry_clips.get())
            clip_duration = float(self.entry_duration.get())
            duration_int = int(clip_duration) 
            
            required_matches = 2 if duration_int >= 2 else 1

            base_video_name = os.path.splitext(os.path.basename(video_path))[0]
            ffmpeg_exe = get_ffmpeg_exe()
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0 or fps <= 0:
                self.log(f"❌ Corrupt video or unreadable FPS: {base_video_name}")
                return

            total_seconds = int(total_frames / fps)
            if total_seconds <= duration_int:
                self.log(f"⚠️ Video is too short: {base_video_name}")
                return
            
            all_seconds = list(range(0, total_seconds - duration_int))
            random.shuffle(all_seconds)

            extracted_clips = 0
            
            # --- SKIP IRRELEVANT VIDEO LOGIC ---
            consecutive_failures = 0
            max_failures_allowed = 70
            # -----------------------------------
            
            self.log(f"🎬 Processing: {base_video_name}")
            
            def check_celeb_at_second(target_sec):
                cap.set(cv2.CAP_PROP_POS_MSEC, target_sec * 1000)
                ret, frame = cap.read()
                if not ret or frame is None: return False

                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        orig_x, orig_y, orig_w, orig_h = x*2, y*2, w*2, h*2
                        y1, y2 = max(0, orig_y-20), min(frame.shape[0], orig_y+orig_h+20)
                        x1, x2 = max(0, orig_x-20), min(frame.shape[1], orig_x+orig_w+20)
                        crop = frame[y1:y2, x1:x2]
                        
                        if crop.shape[0] > 0 and crop.shape[1] > 0:
                            for target_img_path in self.image_paths:
                                try:
                                    with self.ai_lock:
                                        res = DeepFace.verify(img1_path=crop, img2_path=target_img_path, model_name="VGG-Face", enforce_detection=False)
                                    if res["verified"]:
                                        return True
                                except Exception:
                                    pass
                return False

            for sec in all_seconds:
                self.pause_event.wait()
                if not self.is_running:
                    break
                if extracted_clips >= num_clips:
                    break
                
                self.update_status(f"Probing '{base_video_name[:15]}...' at {sec}s mark (Found: {extracted_clips}/{num_clips})")
                
                clip_extracted_in_this_sec = False
                
                if check_celeb_at_second(sec):
                    matches_found = 1
                    
                    if required_matches > 1:
                        for offset in range(1, duration_int):
                            if not self.is_running: break
                            if check_celeb_at_second(sec + offset):
                                matches_found += 1
                                if matches_found >= required_matches:
                                    break 

                    if matches_found >= required_matches and self.is_running:
                        clip_number_str = f"{extracted_clips + 1:02d}"
                        output_filename = os.path.join(self.output_folder, f"{clip_number_str} clip {base_video_name}.mp4")
                        
                        command = [
                            ffmpeg_exe, "-y", "-ss", str(sec), "-i", video_path, 
                            "-t", str(clip_duration), "-c:v", "copy", "-c:a", "copy", output_filename
                        ]
                        
                        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        extracted_clips += 1
                        clip_extracted_in_this_sec = True # Kamyabi mil gayi!
                        
                        self.log(f"✂️ BINGO! Valid presence found. Saved '{clip_number_str} clip'")

                        if self.drive_service:
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    self.log(f"☁️ Uploading to Drive (Attempt {attempt+1}/{max_retries})...")
                                    
                                    folder_id = self.entry_drive_folder.get().strip()
                                    file_metadata = {'name': os.path.basename(output_filename)}
                                    if folder_id:
                                        file_metadata['parents'] = [folder_id]

                                    media = MediaFileUpload(output_filename, mimetype='video/mp4', resumable=True)
                                    
                                    uploaded_file = self.drive_service.files().create(
                                        body=file_metadata, 
                                        media_body=media, 
                                        fields='id'
                                    ).execute()
                                    
                                    self.log(f"✅ Uploaded Successfully! Drive File ID: {uploaded_file.get('id')}")
                                    break 
                                    
                                except Exception as upload_err:
                                    if attempt < max_retries - 1:
                                        self.log(f"⚠️ Connection dropped! Retrying in 3 seconds...")
                                        time.sleep(3)
                                    else:
                                        self.log(f"❌ Upload Failed after 3 attempts: {str(upload_err)}")

                # --- FAIL COUNTER LOGIC ---
                if clip_extracted_in_this_sec:
                    consecutive_failures = 0  # Clip mil gayi toh counter reset
                else:
                    consecutive_failures += 1 # Clip nahi mili toh counter ++
                    
                if consecutive_failures >= max_failures_allowed:
                    self.log(f"⏭️ Skipping '{base_video_name[:20]}...': No match found in {max_failures_allowed} attempts (Irrelevant video).")
                    break # Loop break karo aur agli video par jao
                # --------------------------

        except Exception as e:
            self.log(f"❌ Error in {video_path}: {str(e)}")
            
        finally:
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            gc.collect()

if __name__ == "__main__":
    app = ClipExtractorApp()
    app.mainloop()

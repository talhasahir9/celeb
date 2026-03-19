import customtkinter as ctk
import threading
import os
import cv2
import face_recognition
import subprocess
import requests
from duckduckgo_search import DDGS
from tkinter import messagebox, filedialog
import concurrent.futures
import time
import traceback
import numpy as np
from scipy.io import wavfile

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AIClipperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Master Clipper - Smart Spread Edition")
        self.geometry("950x800")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        os.makedirs("reference_images", exist_ok=True)
        os.makedirs("clips", exist_ok=True)

        self.selected_files = [] 
        self.custom_face1 = None
        self.custom_face2 = None
        self.create_widgets()

    def create_widgets(self):
        # 1. Header
        self.label_title = ctk.CTkLabel(self, text="AI Local Clipper (Audio Heatmap & Smart Spread)", font=ctk.CTkFont(size=22, weight="bold"))
        self.label_title.grid(row=0, column=0, pady=10, sticky="ew")

        # 2. Middle Section
        self.mid_frame = ctk.CTkFrame(self)
        self.mid_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.mid_frame.grid_columnconfigure(0, weight=1)
        self.mid_frame.grid_columnconfigure(1, weight=1)
        self.mid_frame.grid_rowconfigure(0, weight=1)

        # --- Left: Video Selection ---
        self.file_frame = ctk.CTkFrame(self.mid_frame)
        self.file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.btn_browse = ctk.CTkButton(self.file_frame, text="📁 SELECT VIDEOS", command=self.browse_videos, fg_color="#1f538d")
        self.btn_browse.pack(pady=10, padx=10, fill="x")

        self.scroll_list = ctk.CTkScrollableFrame(self.file_frame, label_text="Selected Files")
        self.scroll_list.pack(pady=5, fill="both", expand=True)

        # --- Right: Settings & Faces ---
        self.set_frame = ctk.CTkFrame(self.mid_frame)
        self.set_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.set_frame, text="AI SETTINGS", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        # Face 1 Row
        self.f1_frame = ctk.CTkFrame(self.set_frame, fg_color="transparent")
        self.f1_frame.pack(pady=5, fill="x", padx=10)
        self.entry_c1 = ctk.CTkEntry(self.f1_frame, placeholder_text="Celeb 1 Name", width=160)
        self.entry_c1.pack(side="left", padx=5)
        self.btn_f1 = ctk.CTkButton(self.f1_frame, text="📁 Photo", width=60, command=lambda: self.select_manual_face(1))
        self.btn_f1.pack(side="left")

        # Face 2 Row
        self.f2_frame = ctk.CTkFrame(self.set_frame, fg_color="transparent")
        self.f2_frame.pack(pady=5, fill="x", padx=10)
        self.entry_c2 = ctk.CTkEntry(self.f2_frame, placeholder_text="Celeb 2 (Optional)", width=160)
        self.entry_c2.pack(side="left", padx=5)
        self.btn_f2 = ctk.CTkButton(self.f2_frame, text="📁 Photo", width=60, command=lambda: self.select_manual_face(2))
        self.btn_f2.pack(side="left")

        # NEW: Clip Settings Row (Max Clips & Duration)
        self.clip_set_frame = ctk.CTkFrame(self.set_frame, fg_color="transparent")
        self.clip_set_frame.pack(pady=15, fill="x", padx=10)
        
        self.entry_max_clips = ctk.CTkEntry(self.clip_set_frame, placeholder_text="Max Clips (e.g. 5)", width=130)
        self.entry_max_clips.pack(side="left", padx=5)
        self.entry_max_clips.insert(0, "5") # Default 5 clips

        self.entry_duration = ctk.CTkEntry(self.clip_set_frame, placeholder_text="Duration (sec)", width=130)
        self.entry_duration.pack(side="left", padx=5)
        self.entry_duration.insert(0, "15") # Default 15 sec duration

        self.entry_work = ctk.CTkEntry(self.set_frame, placeholder_text="Workers (1-2)", width=270)
        self.entry_work.pack(pady=10)
        self.entry_work.insert(0, "1")

        # 3. Progress Bar & Log Box
        self.prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.prog_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.prog_label = ctk.CTkLabel(self.prog_frame, text="Progress: 0%")
        self.prog_label.pack(side="left", padx=5)
        self.progress_bar = ctk.CTkProgressBar(self.prog_frame, width=600)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.progress_bar.set(0)

        self.status_log = ctk.CTkTextbox(self, height=120)
        self.status_log.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.status_log.insert("0.0", "System Ready. Please set Max Clips and Clip Duration.\n")

        # 4. START BUTTON
        self.btn_start = ctk.CTkButton(self, text="🚀 START AI CLIPPING", command=self.start_thread, 
                                       fg_color="#28a745", hover_color="#218838", height=50, 
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.btn_start.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

    def log(self, text):
        self.status_log.insert("end", text + "\n")
        self.status_log.see("end")
        self.update_idletasks()

    def select_manual_face(self, num):
        file = filedialog.askopenfilename(title=f"Select Photo for Celeb {num}", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file:
            if num == 1:
                self.custom_face1 = file
                self.btn_f1.configure(text="✅ Loaded", fg_color="green")
                self.log(f"✅ Manual photo loaded for Celeb 1: {os.path.basename(file)}")
            else:
                self.custom_face2 = file
                self.btn_f2.configure(text="✅ Loaded", fg_color="green")
                self.log(f"✅ Manual photo loaded for Celeb 2: {os.path.basename(file)}")

    def browse_videos(self):
        files = filedialog.askopenfilenames(title="Select Video Files", filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.ts")])
        if files:
            self.selected_files = list(files)
            for widget in self.scroll_list.winfo_children(): widget.destroy()
            for path in self.selected_files:
                ctk.CTkLabel(self.scroll_list, text=f"• {os.path.basename(path)}", anchor="w").pack(fill="x", padx=5)
            self.log(f"✅ {len(self.selected_files)} videos selected.")

    def start_thread(self):
        if not self.selected_files:
            messagebox.showerror("Error", "Pehle videos toh select karo!")
            return
        celeb = self.entry_c1.get().strip()
        if not celeb and not self.custom_face1:
            messagebox.showerror("Error", "Celeb 1 ka naam likho ya photo upload karo!")
            return
        
        try:
            max_clips = int(self.entry_max_clips.get().strip())
            clip_dur = int(self.entry_duration.get().strip())
        except:
            messagebox.showerror("Error", "Max Clips aur Duration mein sirf numbers likhein!")
            return
        
        self.btn_start.configure(state="disabled", text="AI IS SCANNING...")
        self.progress_bar.set(0)
        self.prog_label.configure(text="Progress: 0%")
        threading.Thread(target=self.main_workflow, args=(int(self.entry_work.get()), celeb, self.entry_c2.get().strip(), max_clips, clip_dur), daemon=True).start()

    def get_audio_peaks(self, video_path, top_n=15):
        """Method A: Local Audio Heatmap Generator"""
        self.log(f"🎧 Analyzing Audio Energy for {os.path.basename(video_path)}...")
        temp_wav = f"temp_{os.path.basename(video_path)}.wav"
        try:
            # Added -acodec pcm_s16le to ensure scipy can read it properly
            subprocess.run(["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", temp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            samplerate, data = wavfile.read(temp_wav)
            window_size = samplerate * 2 # 2 second windows
            
            energies = []
            for i in range(0, len(data), window_size):
                chunk = data[i:i+window_size]
                energy = np.sqrt(np.mean(chunk.astype(float)**2))
                energies.append((i // samplerate, energy))
                
            energies.sort(key=lambda x: x[1], reverse=True)
            
            peaks = []
            for t, e in energies:
                if not any(abs(t - pt) < 30 for pt in peaks): # Audio peaks ko alag alag rakhna
                    peaks.append(t)
                if len(peaks) >= top_n: break
                
            os.remove(temp_wav)
            self.log(f"🔥 Found {len(peaks)} viral audio moments!")
            return peaks
        except Exception as e:
            self.log(f"⚠️ Audio analysis skipped: {str(e)}")
            if os.path.exists(temp_wav): os.remove(temp_wav)
            return []

    def get_face_encoding(self, name, custom_path):
        save_folder = os.path.join("reference_images", name.replace(' ', '_')) if name else "reference_images/custom"
        os.makedirs(save_folder, exist_ok=True)
        
        encs = []
        if custom_path and os.path.exists(custom_path):
            img = face_recognition.load_image_file(custom_path)
            e = face_recognition.face_encodings(img)
            if e: encs.append(e[0])
            return encs
            
        if len(os.listdir(save_folder)) == 0:
            self.log(f"📥 Fetching faces for {name}...")
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.images(keywords=f"{name} face portrait", max_results=2))
                    for i, res in enumerate(results):
                        img_data = requests.get(res['image'], timeout=10).content
                        with open(os.path.join(save_folder, f"face_{i}.jpg"), 'wb') as f: f.write(img_data)
            except: self.log(f"⚠️ Face download fail for {name}.")
            
        for file in os.listdir(save_folder):
            if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                img = face_recognition.load_image_file(os.path.join(save_folder, file))
                e = face_recognition.face_encodings(img)
                if e: encs.append(e[0])
        return encs

    def main_workflow(self, max_workers, celeb1, celeb2, max_clips, clip_dur):
        try:
            self.log("\n[STEP 1] Starting AI Engine & Faces...")
            encs1 = self.get_face_encoding(celeb1, self.custom_face1)
            encs2 = self.get_face_encoding(celeb2, self.custom_face2) if (celeb2 or self.custom_face2) else []

            if not encs1:
                self.log("❌ Error: Celeb 1 face missing or not detected.")
                return

            self.log(f"\n[STEP 2] Processing {len(self.selected_files)} Videos...")
            
            total_vids = len(self.selected_files)
            
            for index, path in enumerate(self.selected_files):
                self.process_single_video(path, encs1, encs2, max_clips, clip_dur)
                # Overall progress update
                progress = (index + 1) / total_vids
                self.progress_bar.set(progress)
                self.prog_label.configure(text=f"Total Progress: {int(progress*100)}%")

            self.log("\n🎉 ALL DONE! Check the 'clips' folder.")
        except Exception:
            self.log(f"❌ ERROR:\n{traceback.format_exc()}")
        finally:
            self.btn_start.configure(state="normal", text="🚀 START AI CLIPPING")
            self.progress_bar.set(1)

    def process_single_video(self, path, encs1, encs2, max_clips, clip_dur):
        name = os.path.basename(path).split('.')[0]
        
        # 1. Get Viral Audio Peaks
        audio_peaks = self.get_audio_peaks(path, top_n=max_clips + 5)
        
        self.log(f"🔍 Scanning Frames for: {name}...")
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
        
        saved, timestamps = 0, []
        
        # SMART SPREAD LOGIC:
        # Pura video evenly divide karein taake clip har hissay se check ho. (Har 30s ke baad)
        fallback_points = list(range(0, duration, 30))
        
        # Pehle Audio peaks check karega, agar wahan faces na miley toh fallback_points pe jayega
        scan_points = audio_peaks + fallback_points
        
        # Minimum faasla 2 clips ke darmiyan (Taa ke ek hi minute mein saare clips na ban jayein)
        min_gap = clip_dur + 30 
        
        for t in scan_points:
            if saved >= max_clips: break 
            if any(abs(t - st) < min_gap for st in timestamps): continue # Ensures clips are spread out!
            if t >= duration: continue
            
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret: continue
            
            small_frame = cv2.resize(frame, (0,0), fx=0.4, fy=0.4)
            rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            f_encs = face_recognition.face_encodings(rgb, face_recognition.face_locations(rgb))
            
            found1 = any(any(face_recognition.compare_faces(encs1, fe, 0.55)) for fe in f_encs)
            found2 = True if not encs2 else any(any(face_recognition.compare_faces(encs2, fe, 0.55)) for fe in f_encs)
            
            if found1 and found2:
                # 2 second pehle se shuru karna taake reaction poora aaye
                start_time = max(0, t - 2)
                out = os.path.join("clips", f"{name}_clip_{saved+1}.mp4")
                
                # FFMPEG mein aapki di hui Clip Duration (clip_dur) use hogi
                subprocess.run(["ffmpeg", "-y", "-ss", str(start_time), "-i", path, "-t", str(clip_dur), "-c:v", "libx264", "-c:a", "aac", out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                timestamps.append(t)
                saved += 1
                self.log(f"✂️ Viral clip {saved}/{max_clips} saved at {int(t)}s (Duration: {clip_dur}s)")
                
        cap.release()
        self.log(f"✅ Finished: {name}")

if __name__ == "__main__":
    app = AIClipperApp()
    app.mainloop()

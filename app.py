import customtkinter as ctk
import threading
import os
import cv2
import face_recognition
import yt_dlp
import subprocess
import requests
from duckduckgo_search import DDGS
from tkinter import messagebox
import concurrent.futures

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AIClipperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Auto-Clipper Ultimate (Auto-Download & Viral Scan)")
        self.geometry("700x750")
        
        # Safe directory creation
        for folder in ["downloads", "clips", "reference_images"]:
            os.makedirs(folder, exist_ok=True)

        self.create_widgets()

    def create_widgets(self):
        self.label_title = ctk.CTkLabel(self, text="AI Master Clipper Ultimate", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=15)

        self.entry_keyword = ctk.CTkEntry(self, placeholder_text="YouTube Search Keyword (e.g., Jay-Z and Diddy)", width=450)
        self.entry_keyword.pack(pady=5)

        self.entry_limit = ctk.CTkEntry(self, placeholder_text="Total Videos to Scan (e.g., 10)", width=450)
        self.entry_limit.pack(pady=5)

        self.entry_concurrent = ctk.CTkEntry(self, placeholder_text="Simultaneous Processing (e.g., 2)", width=450)
        self.entry_concurrent.pack(pady=5)

        self.label_celeb = ctk.CTkLabel(self, text="Auto-Download Celeb Faces (DuckDuckGo AI)", font=ctk.CTkFont(weight="bold"))
        self.label_celeb.pack(pady=(15, 0))

        self.entry_celeb1 = ctk.CTkEntry(self, placeholder_text="Celeb 1 Name (e.g., Diddy)", width=450)
        self.entry_celeb1.pack(pady=5)

        self.entry_celeb2 = ctk.CTkEntry(self, placeholder_text="Celeb 2 Name (Optional, e.g., Jay-Z)", width=450)
        self.entry_celeb2.pack(pady=5)

        self.status_log = ctk.CTkTextbox(self, width=600, height=200)
        self.status_log.pack(pady=15)
        self.status_log.insert("0.0", "System Initialized. Ready for Zero-Touch Automation...\n")

        self.btn_start = ctk.CTkButton(self, text="Start Full Pipeline", command=self.start_thread, fg_color="green", hover_color="darkgreen")
        self.btn_start.pack(pady=10)

    def log(self, text):
        self.status_log.insert("end", text + "\n")
        self.status_log.see("end")

    def start_thread(self):
        keyword = self.entry_keyword.get().strip()
        limit = self.entry_limit.get().strip()
        concurrent_val = self.entry_concurrent.get().strip()
        celeb1 = self.entry_celeb1.get().strip()
        celeb2 = self.entry_celeb2.get().strip()

        if not keyword or not limit or not concurrent_val or not celeb1:
            messagebox.showerror("Error", "Bhai keyword, limits aur kam az kam Celeb 1 ka naam lazmi do!")
            return

        self.btn_start.configure(state="disabled", text="Pipeline Running...")
        threading.Thread(target=self.main_workflow, args=(keyword, int(limit), int(concurrent_val), celeb1, celeb2), daemon=True).start()

    def auto_download_faces(self, celeb_name):
        save_folder = os.path.join("reference_images", celeb_name.replace(' ', '_'))
        os.makedirs(save_folder, exist_ok=True)
        
        self.log(f"📥 Downloading multiple looks for {celeb_name} (Normal, Sunglasses, Hat, Young, Old)...")
        queries = [
            f"{celeb_name} face clear close up",
            f"{celeb_name} wearing sunglasses face",
            f"{celeb_name} wearing hat cap face",
            f"{celeb_name} young face portrait",
            f"{celeb_name} older recent face portrait"
        ]
        
        downloaded = 0
        with DDGS() as ddgs:
            for i, query in enumerate(queries):
                try:
                    results = list(ddgs.images(keywords=query, max_results=1))
                    if results:
                        image_url = results[0].get('image')
                        img_data = requests.get(image_url, timeout=10).content
                        file_path = os.path.join(save_folder, f"{celeb_name}_look_{i}.jpg")
                        
                        with open(file_path, 'wb') as handler:
                            handler.write(img_data)
                        downloaded += 1
                except Exception as e:
                    self.log(f"Warning: Failed to download 1 image for {celeb_name}.")

        self.log(f"✅ {celeb_name} - {downloaded} images saved for robust AI matching!")
        return save_folder

    def load_folder_encodings(self, folder_path):
        encodings = []
        if not os.path.exists(folder_path): return encodings
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(folder_path, file)
                try:
                    img = face_recognition.load_image_file(img_path)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        encodings.append(encs[0])
                except Exception:
                    pass
        return encodings

    def main_workflow(self, keyword, total_videos, max_workers, celeb1, celeb2):
        try:
            # --- STEP 1: Auto-Download Reference Images ---
            self.log("\n[STEP 1] Auto-Gathering Facial Data...")
            folder1 = self.auto_download_faces(celeb1)
            encodings_c1 = self.load_folder_encodings(folder1)
            
            encodings_c2 = []
            if celeb2:
                folder2 = self.auto_download_faces(celeb2)
                encodings_c2 = self.load_folder_encodings(folder2)

            if not encodings_c1:
                self.log(f"❌ Error: {celeb1} ka face detect nahi hua references mein. Try another name.")
                return

            # --- STEP 2: Search Videos ---
            self.log(f"\n[STEP 2] Searching top {total_videos} videos for '{keyword}'...")
            ydl_opts_search = {'quiet': True, 'extract_flat': True, 'default_search': f'ytsearch{total_videos}'}
            
            video_links = []
            with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
                result = ydl.extract_info(keyword, download=False)
                for entry in result.get('entries', []):
                    video_links.append((entry['id'], entry['url']))

            if not video_links:
                self.log("❌ Koi video nahi mili.")
                return

            # --- STEP 3: Download & Heatmaps ---
            self.log(f"\n[STEP 3] Downloading {len(video_links)} videos & Fetching Viral Heatmaps...")
            downloaded_data = [] 
            
            for index, (vid_id, url) in enumerate(video_links):
                output_file = os.path.join("downloads", f"video_{vid_id}.mp4")
                viral_peaks = []
                
                if not os.path.exists(output_file):
                    self.log(f"Downloading {index+1}/{len(video_links)}: {vid_id}")
                    ydl_opts_dl = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': output_file,
                        'quiet': True,
                        'merge_output_format': 'mp4'
                    }
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                            info = ydl.extract_info(url, download=True)
                            heatmap = info.get('heatmap', [])
                            if heatmap:
                                sorted_heatmap = sorted(heatmap, key=lambda x: x['value'], reverse=True)
                                viral_peaks = [spot['start_time'] for spot in sorted_heatmap[:15]]
                        downloaded_data.append((output_file, viral_peaks))
                    except Exception as e:
                        self.log(f"Skipped {vid_id} due to download error.")
                else:
                    self.log(f"Already downloaded: {vid_id}")
                    downloaded_data.append((output_file, []))

            # --- STEP 4: Smart Processing ---
            self.log(f"\n[STEP 4] Smart AI Scan Start! Ek waqt mein {max_workers} videos...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.process_single_video, data, encodings_c1, encodings_c2) for data in downloaded_data]
                concurrent.futures.wait(futures)

            self.log("\n🎉 ALL DONE! Check 'clips' folder. Best viral clips ready hain.")

        except Exception as e:
            self.log(f"❌ Critical Error: {str(e)}")
        finally:
            self.btn_start.configure(state="normal", text="Start Full Pipeline")

    def process_single_video(self, video_data, encodings_c1, encodings_c2):
        video_path, viral_peaks = video_data
        video_name = os.path.basename(video_path).split('.')[0]
        self.log(f"🔍 Scanning {video_name}...")
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps) if fps else 0

        clips_saved = 0
        saved_timestamps = []
        MIN_GAP = 60 # Anti-clustering gap

        def is_time_valid(t_sec):
            return all(abs(t_sec - st) >= MIN_GAP for st in saved_timestamps)

        def check_faces_at_time(t_sec):
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000)
            ret, frame = cap.read()
            if not ret: return False

            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            frame_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            found_c1 = False
            found_c2 = False if encodings_c2 else True # Agar celeb 2 nahi hai to always true

            for enc in frame_encodings:
                if not found_c1 and any(face_recognition.compare_faces(encodings_c1, enc, tolerance=0.55)):
                    found_c1 = True
                    continue
                if encodings_c2 and not found_c2 and any(face_recognition.compare_faces(encodings_c2, enc, tolerance=0.55)):
                    found_c2 = True

            return found_c1 and found_c2

        # Phase 1: Viral Heatmap
        if viral_peaks:
            for peak in viral_peaks:
                if clips_saved >= 5: break
                if not is_time_valid(peak): continue
                
                for offset in [0, 2, -2]: 
                    check_t = peak + offset
                    if 0 <= check_t <= duration and check_faces_at_time(check_t):
                        out_clip = os.path.join("clips", f"{video_name}_viral_{clips_saved+1}.mp4")
                        self.cut_clip(video_path, max(0, check_t - 2), out_clip)
                        saved_timestamps.append(check_t)
                        clips_saved += 1
                        self.log(f"✂️ Viral clip {clips_saved}/5 saved at {int(check_t)}s")
                        break 

        # Phase 2: Random Fallback
        if clips_saved < 5:
            for t in range(0, duration, 10):
                if clips_saved >= 5: break
                if not is_time_valid(t): continue 

                if check_faces_at_time(t):
                    out_clip = os.path.join("clips", f"{video_name}_random_{clips_saved+1}.mp4")
                    self.cut_clip(video_path, max(0, t - 2), out_clip)
                    saved_timestamps.append(t)
                    clips_saved += 1
                    self.log(f"✂️ Random clip {clips_saved}/5 saved at {t}s")

        cap.release()
        self.log(f"✅ {video_name} done.")

    def cut_clip(self, input_video, start_time, output_path):
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-i", input_video, 
            "-t", "5", "-c:v", "libx264", "-c:a", "aac", output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    app = AIClipperApp()
    app.mainloop()

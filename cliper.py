import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import os
import imageio_ffmpeg
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# UI Setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Jamo's Video Automation Tool")
        self.geometry("700x600")
        
        # Tabs Create Kar Rahe Hain
        self.tabview = ctk.CTkTabview(self, width=650, height=550)
        self.tabview.pack(padx=20, pady=20)
        
        self.tab_clip = self.tabview.add("Video Clipper")
        self.tab_drive = self.tabview.add("Google Drive Uploader")
        
        self.setup_clipper_ui()
        self.setup_drive_ui()

    # ================= CLIPPER LOGIC =================
    def setup_clipper_ui(self):
        self.input_video = None
        self.output_folder = None

        ctk.CTkLabel(self.tab_clip, text="✂️ Video Clipper", font=("Arial", 20, "bold")).pack(pady=10)
        
        self.btn_in = ctk.CTkButton(self.tab_clip, text="Select Video", command=self.select_video)
        self.btn_in.pack(pady=5)
        self.lbl_in = ctk.CTkLabel(self.tab_clip, text="No file selected", text_color="gray")
        self.lbl_in.pack()

        ctk.CTkLabel(self.tab_clip, text="Start Time (HH:MM:SS):").pack(pady=(10,0))
        self.ent_start = ctk.CTkEntry(self.tab_clip, placeholder_text="00:00:00")
        self.ent_start.pack()

        ctk.CTkLabel(self.tab_clip, text="End Time (HH:MM:SS):").pack(pady=(10,0))
        self.ent_end = ctk.CTkEntry(self.tab_clip, placeholder_text="00:00:10")
        self.ent_end.pack()

        self.btn_cut = ctk.CTkButton(self.tab_clip, text="Cut Video", fg_color="green", command=self.process_cut)
        self.btn_cut.pack(pady=20)

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv")])
        if path:
            self.input_video = path
            self.lbl_in.configure(text=os.path.basename(path), text_color="white")

    def process_cut(self):
        if not self.input_video: return
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        out_path = self.input_video.replace(".mp4", "_cut.mp4")
        
        cmd = [ffmpeg_exe, "-i", self.input_video, "-ss", self.ent_start.get(), "-to", self.ent_end.get(), "-c", "copy", "-y", out_path]
        subprocess.run(cmd)
        messagebox.showinfo("Done", f"Video Saved: {out_path}")

    # ================= DRIVE UPLOADER LOGIC =================
    def setup_drive_ui(self):
        ctk.CTkLabel(self.tab_drive, text="☁️ Drive Uploader", font=("Arial", 20, "bold")).pack(pady=10)

        ctk.CTkLabel(self.tab_drive, text="Enter Google Drive Folder ID:").pack(pady=(10,0))
        self.ent_folder_id = ctk.CTkEntry(self.tab_drive, width=400, placeholder_text="Paste Folder ID here...")
        self.ent_folder_id.pack(pady=5)

        self.btn_sel_drive = ctk.CTkButton(self.tab_drive, text="Select File to Upload", command=self.select_drive_file)
        self.btn_sel_drive.pack(pady=10)
        self.lbl_drive_file = ctk.CTkLabel(self.tab_drive, text="No file selected", text_color="gray")
        self.lbl_drive_file.pack()

        self.btn_upload = ctk.CTkButton(self.tab_drive, text="Upload to Drive", fg_color="#1f538d", command=self.upload_to_drive)
        self.btn_upload.pack(pady=20)
        
        self.status_drive = ctk.CTkLabel(self.tab_drive, text="")
        self.status_drive.pack()

    def select_drive_file(self):
        self.upload_file_path = filedialog.askopenfilename()
        if self.upload_file_path:
            self.lbl_drive_file.configure(text=os.path.basename(self.upload_file_path), text_color="white")

    def upload_to_drive(self):
        folder_id = self.ent_folder_id.get().strip()
        if not folder_id or not hasattr(self, 'upload_file_path'):
            messagebox.showerror("Error", "Folder ID aur File dono zaroori hain!")
            return

        try:
            self.status_drive.configure(text="Uploading...", text_color="yellow")
            self.update()

            # token.json se authenticate karna
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.file'])
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {
                'name': os.path.basename(self.upload_file_path),
                'parents': [folder_id]
            }
            media = MediaFileUpload(self.upload_file_path, resumable=True)
            
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            self.status_drive.configure(text=f"✅ Uploaded! ID: {file.get('id')}", text_color="green")
            messagebox.showinfo("Success", "File Drive par upload ho gayi!")
            
        except Exception as e:
            self.status_drive.configure(text="❌ Upload Failed", text_color="red")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = AutomationApp()
    app.mainloop()

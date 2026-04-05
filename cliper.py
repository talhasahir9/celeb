import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import os
import imageio_ffmpeg  # Nayi library import ki

# Theme aur UI setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProVideoClipper(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pro Video Clipper Dashboard")
        self.geometry("600x550")
        self.resizable(False, False)
        
        self.input_video_path = None
        self.output_folder_path = None

        # --- Title ---
        self.title_label = ctk.CTkLabel(self, text="✂️ Video Clipper Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 20))

        # --- File Selection Section ---
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.pack(fill="x", padx=40, pady=10)

        # Input Video
        self.btn_input = ctk.CTkButton(self.file_frame, text="1. Select Video File", command=self.select_input_video, width=200)
        self.btn_input.grid(row=0, column=0, pady=10, sticky="w")
        self.lbl_input = ctk.CTkLabel(self.file_frame, text="No video selected...", text_color="gray", width=300, anchor="w")
        self.lbl_input.grid(row=0, column=1, padx=20, pady=10)

        # Output Folder
        self.btn_output = ctk.CTkButton(self.file_frame, text="2. Select Output Folder", command=self.select_output_folder, width=200)
        self.btn_output.grid(row=1, column=0, pady=10, sticky="w")
        self.lbl_output = ctk.CTkLabel(self.file_frame, text="No folder selected...", text_color="gray", width=300, anchor="w")
        self.lbl_output.grid(row=1, column=1, padx=20, pady=10)

        # --- Timestamps Section ---
        self.time_frame = ctk.CTkFrame(self)
        self.time_frame.pack(pady=20, padx=40, fill="x")

        self.time_title = ctk.CTkLabel(self.time_frame, text="Set Timestamps (HH:MM:SS)", font=ctk.CTkFont(weight="bold"))
        self.time_title.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # Start Time
        self.lbl_start = ctk.CTkLabel(self.time_frame, text="Start Time:")
        self.lbl_start.grid(row=1, column=0, padx=(30, 10), pady=10, sticky="e")
        self.entry_start = ctk.CTkEntry(self.time_frame, placeholder_text="00:00:00", width=150, justify="center")
        self.entry_start.grid(row=1, column=1, padx=(0, 30), pady=10)

        # End Time
        self.lbl_end = ctk.CTkLabel(self.time_frame, text="End Time:")
        self.lbl_end.grid(row=2, column=0, padx=(30, 10), pady=(0, 20), sticky="e")
        self.entry_end = ctk.CTkEntry(self.time_frame, placeholder_text="00:00:00", width=150, justify="center")
        self.entry_end.grid(row=2, column=1, padx=(0, 30), pady=(0, 20))

        # --- Process Section ---
        self.btn_process = ctk.CTkButton(self, text="Start Processing", command=self.process_video, 
                                         fg_color="#28a745", hover_color="#218838", 
                                         height=45, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_process.pack(pady=(10, 10))

        # Status Label
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="white", font=ctk.CTkFont(size=14))
        self.lbl_status.pack()

    def select_input_video(self):
        file_path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")])
        if file_path:
            self.input_video_path = file_path
            self.lbl_input.configure(text=self.truncate_path(file_path), text_color="white")
            
            if not self.output_folder_path:
                self.output_folder_path = os.path.dirname(file_path)
                self.lbl_output.configure(text=self.truncate_path(self.output_folder_path), text_color="white")

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder_path = folder_path
            self.lbl_output.configure(text=self.truncate_path(folder_path), text_color="white")

    def truncate_path(self, path, max_length=35):
        if len(path) > max_length:
            return "..." + path[-(max_length-3):]
        return path

    def process_video(self):
        if not self.input_video_path:
            messagebox.showerror("Error", "Bhai pehle Video toh select karo!")
            return
        if not self.output_folder_path:
            messagebox.showerror("Error", "Output folder select nahi kiya!")
            return

        start_time = self.entry_start.get().strip()
        end_time = self.entry_end.get().strip()

        if not start_time or not end_time:
            messagebox.showerror("Error", "Start aur End time dono daalna zaroori hai (Format: 00:00:00)")
            return

        base_name = os.path.basename(self.input_video_path)
        name, ext = os.path.splitext(base_name)
        output_file_name = f"{name}_cut{ext}"
        output_full_path = os.path.join(self.output_folder_path, output_file_name)

        try:
            self.lbl_status.configure(text="Preparing FFmpeg...", text_color="yellow")
            self.update()

            # Yahan hum imageio-ffmpeg se exe ka path le rahe hain
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            # Command mein ab 'ffmpeg' ki jagah seedha us exe ka path jayega
            command = [
                ffmpeg_exe,
                "-i", self.input_video_path,
                "-ss", start_time,
                "-to", end_time,
                "-c", "copy",
                "-y",  
                output_full_path
            ]

            self.lbl_status.configure(text="Cutting video, please wait...")
            self.update()

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                self.lbl_status.configure(text=f"✅ Video Saved Successfully!\nPath: {output_full_path}", text_color="#28a745")
                messagebox.showinfo("Success", f"Video cut ho kar yahan save ho gayi hai:\n{self.output_folder_path}")
            else:
                self.lbl_status.configure(text="❌ Error occurred!", text_color="red")
                print("FFmpeg Error:", result.stderr)
                messagebox.showerror("Error", "Video cut nahi ho saki. Time format check karein (00:00:00).")

        except Exception as e:
            messagebox.showerror("System Error", f"Kuch masla ho gaya: {str(e)}")
            self.lbl_status.configure(text="Error processing video!", text_color="red")

if __name__ == "__main__":
    app = ProVideoClipper()
    app.mainloop()

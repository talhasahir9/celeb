# ✂️ AI Master Clipper Ultimate - Smart Spread Edition

Yeh ek advanced AI-powered Python application hai jo aapki local videos (Podcasts, Interviews, Vlogs) ko scan karti hai aur automatically best "Viral Clips" nikaal kar deti hai. Yeh **Audio Energy (Heatmap)** aur **Facial Recognition** ka istemal karti hai taake sirf wahi clips banein jahan action ho aur aapka target Celeb mojood ho.

---

## 🛑 PHASE 1: FFmpeg Setup (Sab Se Zaroori Hissa)

Python script video kaatne aur audio nikalne ke liye background mein `FFmpeg` use karti hai. Agar yeh nahi hoga toh script clips nahi bana payegi.

1. **Download:** [FFmpeg Windows Builds](https://www.gyan.dev/ffmpeg/builds/) se `ffmpeg-git-full.7z` ya zip download karein.
2. **Extract:** Zip file ko extract karein aur folder ka naam `ffmpeg` rakh kar apni `C:\` drive mein paste kar dein (e.g., `C:\ffmpeg`).
3. **Add to PATH:** * Windows search mein likhein "Environment Variables".
   * "System Variables" mein `Path` ko edit karein.
   * "New" par click karein aur `C:\ffmpeg\bin` add kar dein.
   * Sab OK kar ke band kar dein.
4. **Verify:** Naya CMD kholein aur `ffmpeg -version` likh kar enter karein. Agar detail aa jaye toh kaam set hai!

---

## 🛠️ PHASE 2: Python Dependencies (The 100% Working Bypass Method)

Windows par `dlib` aur `face_recognition` install karte waqt "C++ Build Tools" aur "CMake" ke azaab se bachne ke liye yeh exact steps CMD mein bari bari run karein (Make sure aap Python 3.12 use kar rahe hain):

**Step 1: Fix Core Tools (Setuptools downgrade)**
```bash
pip install setuptools==70.0.0 wheel cmake



Gemini said
Lo Jamo bhai, yeh raha aapka 100% Fresh aur Final README.md. Ismein wahi exact, tested tareeqa likha hai jis se aapka masla hal hua (bina C++ compile kiye direct Wheel link aur Git wala fix).

Is poore text ko copy kar ke apne folder mein README.md ke naam se save kar lo. Zindagi mein kabhi naye server ya PC par setup karna ho toh bas yeh file dekhni padegi!

Markdown
# ✂️ AI Master Clipper Ultimate - Smart Spread Edition

Yeh ek advanced AI-powered Python application hai jo aapki local videos (Podcasts, Interviews, Vlogs) ko scan karti hai aur automatically best "Viral Clips" nikaal kar deti hai. Yeh **Audio Energy (Heatmap)** aur **Facial Recognition** ka istemal karti hai taake sirf wahi clips banein jahan action ho aur aapka target Celeb mojood ho.

---

## 🛑 PHASE 1: FFmpeg Setup (Sab Se Zaroori Hissa)

Python script video kaatne aur audio nikalne ke liye background mein `FFmpeg` use karti hai. Agar yeh nahi hoga toh script clips nahi bana payegi.

1. **Download:** [FFmpeg Windows Builds](https://www.gyan.dev/ffmpeg/builds/) se `ffmpeg-git-full.7z` ya zip download karein.
2. **Extract:** Zip file ko extract karein aur folder ka naam `ffmpeg` rakh kar apni `C:\` drive mein paste kar dein (e.g., `C:\ffmpeg`).
3. **Add to PATH:** * Windows search mein likhein "Environment Variables".
   * "System Variables" mein `Path` ko edit karein.
   * "New" par click karein aur `C:\ffmpeg\bin` add kar dein.
   * Sab OK kar ke band kar dein.
4. **Verify:** Naya CMD kholein aur `ffmpeg -version` likh kar enter karein. Agar detail aa jaye toh kaam set hai!

---

## 🛠️ PHASE 2: Python Dependencies (The 100% Working Bypass Method)

Windows par `dlib` aur `face_recognition` install karte waqt "C++ Build Tools" aur "CMake" ke azaab se bachne ke liye yeh exact steps CMD mein bari bari run karein (Make sure aap Python 3.12 use kar rahe hain):

**Step 1: Fix Core Tools (Setuptools downgrade)**
```bash
pip install setuptools==70.0.0 wheel cmake
Step 2: Install Dlib via Pre-compiled Wheel (Direct Bypass)
(Yeh file direct internet se aayegi, compiling ki zaroorat nahi padegi)

Bash
pip install [https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl](https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.99-cp312-cp312-win_amd64.whl)
Step 3: Install Face Recognition via Git

Bash
pip install git+[https://github.com/ageitgey/face_recognition.git](https://github.com/ageitgey/face_recognition.git)
Step 4: Install Remaining UI & AI Libraries

Bash
pip install customtkinter opencv-python duckduckgo-search scipy numpy requests
🎉 Bas! Aapka environment bilkul ready hai.

🚀 PHASE 3: How to Use (Istemal Ka Tareeqa)
Apne folder mein ek file banayein app.py aur neechay diya gaya code usme paste kar dein.

Apne terminal ya CMD mein likhein:

Bash
python app.py
Software khulne ke baad:

📁 SELECT VIDEOS: PC se videos (.mp4, .mkv) choose karein.

Celeb Setup: Right side par Celeb 1 Name likhein (e.g., Diddy) ya phir 📁 Photo daba kar uski tasveer apne PC se upload karein.

Clip Settings: Max Clips aur Duration set karein (e.g., 5 clips, 30 seconds each).

🚀 START AI CLIPPING: Button daba dein!

AI apna kaam shuru karega: Pehle Audio peaks dhoondega, phir frames scan karega, aur evenly spread karke clips clips folder mein save kar dega.

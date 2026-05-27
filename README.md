# ⚡ VibeCut — AI Beat-Synced Video Editor

VibeCut automatically edits your video clips to sync cuts perfectly with music beats, then applies cinematic color grading — all in one click.

---

## ✨ Features

- 🎵 **Beat detection** — librosa detects every beat in your track
- 🎬 **Scene analysis** — PySceneDetect finds key moments in your video
- ✂️ **Beat-synced cuts** — clips are cut exactly on the beat
- 🎨 **3 Templates** — Hype · Anime · Cinematic (color grades via FFmpeg)
- ⬇️ **Instant download** — processed MP4 ready to post

---

## 🗂️ Project Structure

```
vibecut/
├── backend/
│   ├── main.py            ← FastAPI server
│   ├── beat_detector.py   ← librosa beat analysis
│   ├── scene_detect.py    ← PySceneDetect scene detection
│   ├── video_engine.py    ← MoviePy + FFmpeg rendering
│   └── requirements.txt
├── frontend/
│   ├── index.html         ← Main UI
│   ├── style.css          ← Dark cinematic styles
│   └── app.js             ← Upload + progress logic
└── README.md
```

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.10+
- FFmpeg installed on your system
- Git

### 1. Install FFmpeg

**Windows:**
```
winget install ffmpeg
```
Or download from https://ffmpeg.org/download.html and add to PATH.

**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

### 2. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/vibecut.git
cd vibecut
```

### 3. Set up Python backend
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the backend
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend is now running at: `http://localhost:8000`

### 5. Open the frontend
Open `frontend/index.html` directly in your browser.

> If you get CORS issues, run a simple HTTP server:
> ```bash
> cd frontend
> python -m http.server 3000
> ```
> Then open `http://localhost:3000`

---

## 🎬 How to Use

1. **Upload your video** — MP4, MOV, AVI, MKV supported
2. **Upload your music** — MP3, WAV, M4A, AAC supported
3. **Pick a template** — Hype / Anime / Cinematic
4. **Click CREATE MY EDIT** — wait 1–3 minutes
5. **Download** your beat-synced edit 🔥

---

## 🎨 Templates

| Template | Style | Cuts | Color Grade |
|----------|-------|------|-------------|
| ⚡ Hype | High energy, high contrast | Every beat | Boosted contrast + saturation |
| 🌸 Anime | Warm, saturated, flash transitions | Every beat | Warm hue shift + saturation |
| 🎞️ Cinematic | Slow, filmic | Every 2 beats | Teal-orange film grade |

---

## 🌐 Deploy (Optional)

**Backend** → Deploy to [Railway](https://railway.app) or [Render](https://render.com) (free tier available)

**Frontend** → Deploy to [Vercel](https://vercel.com) or [Netlify](https://netlify.com) (free)

After deploying, update `API_BASE` in `frontend/app.js` to your backend URL.

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python · FastAPI · uvicorn |
| Beat Detection | librosa |
| Scene Detection | PySceneDetect |
| Video Rendering | MoviePy |
| Color Grading | FFmpeg |
| Frontend | HTML · CSS · Vanilla JS |

---

## 📝 License

MIT — free to use and modify.

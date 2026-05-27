"""
VibeCut — AI Video Editor Backend
FastAPI server that handles video uploads and processing jobs.
"""

import os
import shutil
import uuid
from pathlib import Path
from threading import Thread

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from beat_detector import detect_beats
from scene_detect import detect_scenes
from video_engine import apply_template, get_template_info

# ─────────────────────────────────────────
#  APP SETUP
# ─────────────────────────────────────────
app = FastAPI(title="VibeCut API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Serve rendered videos as static files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# In-memory job store  {job_id: {status, progress, message, output_url, error}}
jobs: dict = {}


# ─────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "VibeCut API is running 🎬", "version": "1.0.0"}


@app.get("/templates")
def list_templates():
    return {"templates": get_template_info()}


@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    template: str = Form(default="hype"),
):
    """
    Upload a video + audio file, kick off the editing pipeline.
    Returns a job_id to poll for status.
    """
    job_id = str(uuid.uuid4())

    # Validate extensions
    allowed_video = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    allowed_audio = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}

    vid_ext = Path(video.filename).suffix.lower()
    aud_ext = Path(audio.filename).suffix.lower()

    if vid_ext not in allowed_video:
        raise HTTPException(400, f"Video format '{vid_ext}' not supported.")
    if aud_ext not in allowed_audio:
        raise HTTPException(400, f"Audio format '{aud_ext}' not supported.")

    # Save files to disk
    video_path = UPLOAD_DIR / f"{job_id}_video{vid_ext}"
    audio_path = UPLOAD_DIR / f"{job_id}_audio{aud_ext}"

    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    # Initialise job record
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Job queued…",
        "output_url": None,
        "error": None,
    }

    # Run in background thread so we don't block
    thread = Thread(
        target=_run_pipeline,
        args=(job_id, str(video_path), str(audio_path), template),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Poll this endpoint to get progress updates."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


@app.get("/download/{job_id}")
def download_video(job_id: str):
    """Direct download endpoint for the processed video."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Video not ready yet")
    output_path = OUTPUT_DIR / f"{job_id}_output.mp4"
    if not output_path.exists():
        raise HTTPException(404, "Output file not found")
    return FileResponse(str(output_path), media_type="video/mp4", filename="vibecut_edit.mp4")


# ─────────────────────────────────────────
#  PIPELINE (runs in background thread)
# ─────────────────────────────────────────
def _run_pipeline(job_id: str, video_path: str, audio_path: str, template: str):
    def update(pct: int, msg: str):
        jobs[job_id]["progress"] = pct
        jobs[job_id]["message"] = msg

    try:
        jobs[job_id]["status"] = "processing"
        update(5, "Analysing audio beats…")

        beats = detect_beats(audio_path)
        update(25, f"Found {len(beats['beat_times'])} beats at {beats['tempo']:.0f} BPM")

        update(35, "Detecting scenes…")
        scenes = detect_scenes(video_path)
        update(45, f"Found {len(scenes)} scenes")

        output_path = str(OUTPUT_DIR / f"{job_id}_output.mp4")
        update(50, "Applying template…")

        apply_template(
            video_path=video_path,
            audio_path=audio_path,
            beat_times=beats["beat_times"],
            scenes=scenes,
            template=template,
            output_path=output_path,
            on_progress=lambda p, m: update(50 + int(p * 0.5), m),
        )

        jobs[job_id]["status"] = "done"
        jobs[job_id]["output_url"] = f"/outputs/{job_id}_output.mp4"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Your edit is ready! 🔥"

        # Clean up uploads to save space
        _cleanup_uploads(job_id, video_path, audio_path)

    except Exception as exc:
        import traceback
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(exc)
        jobs[job_id]["message"] = f"Error: {exc}"
        print(f"[Pipeline ERROR] {job_id}:\n{traceback.format_exc()}")


def _cleanup_uploads(job_id: str, *paths):
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

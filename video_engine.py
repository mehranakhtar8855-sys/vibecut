import os
import subprocess
from pathlib import Path

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx,
)

# ─────────────────────────────────────────
#  TEMPLATE DEFINITIONS
# ─────────────────────────────────────────
TEMPLATES = {
    "anime": {
        "label": "Anime",
        "cut_every_n_beats": 1,       # cut on every single beat — fast
        "ffmpeg_vf": (
            "eq=saturation=1.8:contrast=1.15,"
            "hue=h=8,"                # slight warm shift
            "curves=all='0/0 0.45/0.5 1/1'"
        ),
        "speed": 1.0,
        "flash_transition": True,
    },
    "cinematic": {
        "label": "Cinematic",
        "cut_every_n_beats": 2,       # slower, breathes more
        "ffmpeg_vf": (
            "curves="
            "r='0/0 0.5/0.42 1/0.82':"
            "g='0/0 0.5/0.5 1/0.9':"
            "b='0/0.08 0.5/0.48 1/0.72',"  # teal-orange grade
            "eq=contrast=1.05:brightness=-0.02"
        ),
        "speed": 1.0,
        "flash_transition": False,
    },
    "hype": {
        "label": "Hype",
        "cut_every_n_beats": 1,
        "ffmpeg_vf": (
            "eq=contrast=1.35:brightness=0.04:saturation=1.9,"
            "curves=all='0/0 0.3/0.35 0.7/0.75 1/1'"
        ),
        "speed": 1.0,
        "flash_transition": True,
    },
}


# ─────────────────────────────────────────
#  MAIN PIPELINE
# ─────────────────────────────────────────
def apply_template(
    video_path: str,
    audio_path: str,
    beat_times: list,
    scenes: list,
    template: str,
    output_path: str,
    on_progress=None,
) -> str:
    """
    Full pipeline:
    1. Slice the source video at beat-sync cut points
    2. Concatenate clips
    3. Replace audio with the provided music track
    4. Apply FFmpeg color-grade pass
    """
    cfg = TEMPLATES.get(template, TEMPLATES["hype"])
    temp_raw = output_path.replace(".mp4", "_raw.mp4")

    _report(on_progress, 5, "Loading video…")
    video = VideoFileClip(video_path)
    vid_duration = video.duration

    # ── Step 1: Pick cut points from beat times ──────────────────────────────
    every_n = cfg["cut_every_n_beats"]
    cut_points = beat_times[::every_n]

    # Make sure we have at least 2 points
    if len(cut_points) < 2:
        cut_points = beat_times if len(beat_times) >= 2 else [0, vid_duration]

    _report(on_progress, 20, "Syncing cuts to beats…")

    # ── Step 2: Build clips ───────────────────────────────────────────────────
    clips = []
    for i in range(len(cut_points) - 1):
        beat_start = cut_points[i]
        beat_end = cut_points[i + 1]
        segment_len = beat_end - beat_start

        # Source position: loop the video if needed
        src_start = beat_start % vid_duration
        src_end = src_start + segment_len

        # Clamp to video duration
        if src_end > vid_duration:
            src_end = vid_duration
        if src_start >= src_end:
            continue

        try:
            clip = video.subclip(src_start, src_end)
            # Optional: flash frame (white) at start for hype/anime
            if cfg["flash_transition"] and i > 0:
                flash = clip.subclip(0, min(0.05, clip.duration)).fx(vfx.colorx, 3.0)
                clip = concatenate_videoclips([flash, clip.subclip(0.05)])
            clips.append(clip)
        except Exception as e:
            print(f"[VideoEngine] Skipping clip {i}: {e}")
            continue

    if not clips:
        print("[VideoEngine] No clips generated — using full video as fallback")
        clips = [video]

    _report(on_progress, 45, "Assembling clips…")

    # ── Step 3: Concatenate ──────────────────────────────────────────────────
    final_video = concatenate_videoclips(clips, method="compose")

    # ── Step 4: Attach audio ─────────────────────────────────────────────────
    _report(on_progress, 55, "Mixing audio…")
    audio = AudioFileClip(audio_path)
    if audio.duration > final_video.duration:
        audio = audio.subclip(0, final_video.duration)
    else:
        # Trim video to audio length
        final_video = final_video.subclip(0, min(final_video.duration, audio.duration))
    final_video = final_video.set_audio(audio)

    # ── Step 5: Write intermediate file ─────────────────────────────────────
    _report(on_progress, 65, "Rendering…")
    final_video.write_videofile(
        temp_raw,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        verbose=False,
        logger=None,
    )

    # Close clips to free memory
    video.close()
    final_video.close()
    audio.close()

    # ── Step 6: Color-grade pass via FFmpeg ──────────────────────────────────
    _report(on_progress, 85, "Applying color grade…")
    _ffmpeg_color_grade(temp_raw, output_path, cfg["ffmpeg_vf"])

    # Cleanup temp
    if os.path.exists(temp_raw):
        os.remove(temp_raw)

    _report(on_progress, 100, "Done!")
    print(f"[VideoEngine] Output saved: {output_path}")
    return output_path


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def _ffmpeg_color_grade(input_path: str, output_path: str, vf_filter: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[FFmpeg] Warning: {result.stderr[-500:]}")
        # Fall back: just copy the file
        import shutil
        shutil.copy(input_path, output_path)


def _report(callback, pct: int, msg: str):
    print(f"[VideoEngine] {pct}% — {msg}")
    if callback:
        callback(pct, msg)


def get_template_info() -> list:
    return [
        {"id": k, "label": v["label"]}
        for k, v in TEMPLATES.items()
    ]

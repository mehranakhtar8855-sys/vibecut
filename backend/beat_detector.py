import librosa
import numpy as np


def detect_beats(audio_path: str) -> dict:
    """
    Detect beats in an audio file and return timestamps.
    Uses librosa for BPM analysis and onset detection.
    """
    print(f"[BeatDetector] Loading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=None, mono=True)

    # Detect tempo and beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # Detect onsets (for emphasis / drop moments)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, backtrack=False
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

    duration = float(len(y) / sr)

    print(f"[BeatDetector] BPM: {float(tempo):.1f} | Beats: {len(beat_times)} | Duration: {duration:.1f}s")

    return {
        "tempo": float(tempo),
        "beat_times": beat_times,
        "onset_times": onset_times,
        "duration": duration,
    }


def get_cut_points(beat_times: list, every_n_beats: int = 1, max_cuts: int = 60) -> list:
    """
    Reduce beat times to a manageable set of cut points.
    """
    cuts = beat_times[::every_n_beats]
    return cuts[:max_cuts]

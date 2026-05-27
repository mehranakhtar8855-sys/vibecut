from scenedetect import detect, ContentDetector, AdaptiveDetector


def detect_scenes(video_path: str, threshold: float = 27.0) -> list:
    """
    Detect scene changes in a video file.
    Returns a list of scenes with start/end timestamps.
    """
    print(f"[SceneDetect] Analysing: {video_path}")

    try:
        scene_list = detect(video_path, ContentDetector(threshold=threshold))
    except Exception as e:
        print(f"[SceneDetect] ContentDetector failed: {e}. Falling back to AdaptiveDetector.")
        scene_list = detect(video_path, AdaptiveDetector())

    scenes = []
    for i, scene in enumerate(scene_list):
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        scenes.append(
            {
                "scene_num": i + 1,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(end - start, 3),
            }
        )

    print(f"[SceneDetect] Found {len(scenes)} scenes")
    return scenes


def get_best_moments(scenes: list, count: int = 20) -> list:
    """
    Pick the most interesting moments from detected scenes.
    Prioritises variety — picks the middle of longer scenes.
    """
    if not scenes:
        return []

    # Sort by duration descending, pick top scenes
    sorted_scenes = sorted(scenes, key=lambda s: s["duration"], reverse=True)
    top = sorted_scenes[:count]

    # Return the midpoint of each good scene
    moments = [round((s["start"] + s["end"]) / 2, 3) for s in top]
    moments.sort()
    return moments

"""Deterministic timeline for animation/make_video.py (pure Python, no Blender needed).

Everything time-based lives here so it can be unit-tested and shared by Blender (shots, motion)
and FFmpeg (captions). Times are in seconds; frames are derived from fps.
"""
import argparse
import json
import sys

DEFAULT_CAPTION = "Meet the Forge crew | walking in | say hello | jump for joy"

# Camera shots as fractions of the duration. Positions are in character heights (h), relative to the
# character at the origin, which faces -Y (Blender). (start, end, cam_from, cam_to, look_at_z)
SHOTS = [
    (0.0, 1 / 3, (0.6, -4.2, 0.55), (0.25, -3.6, 0.6), 0.5),     # 1: wide, low front, slow dolly in
    (1 / 3, 2 / 3, (-2.6, -2.2, 1.9), (2.6, -2.4, 1.7), 0.45),   # 2: high three-quarter orbit, left to right
    (2 / 3, 1.0, (-0.3, -2.4, 0.75), (0.0, -1.5, 0.7), 0.6),     # 3: close-up push-in
]


def shot_frames(fps, duration):
    """[(first_frame, last_frame, cam_from, cam_to, look_z)] with 1-based inclusive frames, no gaps."""
    total = round(fps * duration)
    out = []
    for s, e, a, b, z in SHOTS:
        out.append((round(s * total) + 1, round(e * total), a, b, z))
    return out


def caption_words(text, duration):
    """Split 'phrase | phrase' captions into one word per slot spread over the duration.

    Returns [(word, start_s, end_s)]; each word stays until the next one appears.
    """
    words = [w for w in text.replace("|", " ").split() if w]
    if not words:
        return []
    step = duration / len(words)
    return [(w, round(i * step, 3), round((i + 1) * step, 3)) for i, w in enumerate(words)]


def drawtext_filter(text, duration, font, height):
    """FFmpeg filter chain: yellow outlined uppercase word, shown only during its slot."""
    size = max(16, round(height * 0.045))
    parts = []
    for w, s, e in caption_words(text, duration):
        safe = w.upper().replace("\\", "").replace("'", "").replace(":", "").replace("%", "")
        parts.append(
            f"drawtext=fontfile={font}:text='{safe}':fontcolor=#FFE100:fontsize={size}"
            f":borderw={max(2, size // 12)}:bordercolor=black:x=(w-text_w)/2:y=h*0.68"
            f":enable='between(t,{s},{e})'")
    return ",".join(parts) or "null"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--caption", default=DEFAULT_CAPTION)
    p.add_argument("--duration", type=float, default=8)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    p.add_argument("--height", type=int, default=1280)
    p.add_argument("--print", choices=["filter", "json"], default="filter")
    a = p.parse_args()
    if a.print == "filter":
        sys.stdout.write(drawtext_filter(a.caption, a.duration, a.font, a.height))
    else:
        json.dump({"shots": shot_frames(a.fps, a.duration), "captions": caption_words(a.caption, a.duration)},
                  sys.stdout, indent=1)

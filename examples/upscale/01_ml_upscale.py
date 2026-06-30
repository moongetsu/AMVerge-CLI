import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from amverge import upscale_video, QUALITY_PRESETS, UPSCALE_AVAILABLE

video_path = sys.argv[1] if len(sys.argv) > 1 else "episode.mp4"
output_path = "upscaled_ml.mp4"

if not Path(video_path).exists():
    print(f"Video not found: {video_path}")
    sys.exit(1)

if not UPSCALE_AVAILABLE:
    print("ML upscaling not available. Run: pip install amverge[upscale]")
    print("This requires: torch, opencv-python-headless, spandrel==0.3.4")
    sys.exit(1)

print(f"Upscaling: {video_path} -> {output_path}")
print(f"Model: adore, Scale: 2x, Preset: {QUALITY_PRESETS['high']['x264']}")
print(f"CRF: {QUALITY_PRESETS['high']['crf']}")

upscale_video(
    video_path,
    output_path,
    model_name="adore",
    scale=2,
    preset="high",
    progress_cb=lambda pct, msg: print(f"[{pct}%] {msg}"),
)

print(f"Done: {output_path}")

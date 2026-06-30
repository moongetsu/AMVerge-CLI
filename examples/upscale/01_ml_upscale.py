import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from amverge import upscale_model, QUALITY_PRESETS, UPSCALE_AVAILABLE, UPSCALE_REGISTRY

video_path = sys.argv[1] if len(sys.argv) > 1 else "episode.mp4"
output_path = "upscaled_ml.mp4"

if not Path(video_path).exists():
    print(f"Video not found: {video_path}")
    sys.exit(1)

if not UPSCALE_AVAILABLE:
    print("ML upscaling not available. Run: pip install amverge[upscale]")
    sys.exit(1)

model_key = "adore"
entry = UPSCALE_REGISTRY[model_key]
print(f"Model: {entry['name']} ({entry['description']})")
print(f"Credit: {entry['credit']}")
print(f"Scales: {entry['scales']}")
print(f"Preset: high (CRF {QUALITY_PRESETS['high']['crf']}, {QUALITY_PRESETS['high']['x264']})")
print()

start_time = time.time()
frame_count = [0]

def progress_cb(pct, msg):
    frame_count[0] = frame_count[0] + 1 if pct > 0 else frame_count[0]
    elapsed = time.time() - start_time
    if pct > 0 and pct < 100:
        eta = (elapsed / pct) * (100 - pct)
        print(f"\r[{pct:3d}%] {msg:40s}  ETA: {eta:5.1f}s", end="")
    else:
        print(f"\r[{pct:3d}%] {msg:40s}", end="")

upscale_model(
    model_key,
    video_path,
    output_path,
    scale=2,
    preset="high",
    progress_cb=progress_cb,
)

elapsed = time.time() - start_time
print(f"\nDone in {elapsed:.1f}s: {output_path}")

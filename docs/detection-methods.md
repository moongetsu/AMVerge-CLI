# Detection Methods

AMVerge CLI supports two scene detection methods. The right choice depends on your source material.

---

## Keyframe (`--method keyframe`)

**Default. Recommended for most content.**

Extracts I-frame (keyframe) timestamps from the video using PyAV packet demux.  
Splits the video at those timestamps with FFmpeg stream copy - no re-encode.

**How it works:**

```txt
PyAV packet demux
      ↓
I-frame timestamps
      ↓
merge short scenes (< min_duration)
      ↓
ffmpeg -segment_times (stream copy)
```

**Pros:**

- Very fast - no frame decoding on the detection pass
- Lossless output - stream copy only
- Works well for anime and broadcast content (I-frames land on scene cuts)

**Cons:**

- Accuracy depends on encoder. Some encodes place I-frames in unusual positions, creating short or near-duplicate clips
- Use the `--min-duration` flag and the similarity check to clean these up

---

## Edge (`--method edge`)

**More accurate. Requires OpenCV.**

```bash
pip install amverge[edge]
```

Decodes every frame and runs Canny edge detection + cosine similarity comparison between adjacent frames. Detects cut boundaries by large shifts in edge density.

**How it works:**

```txt
PyAV full decode
      ↓
Canny edge map per frame
      ↓
cosine similarity between adjacent frames
      ↓
flag frames where similarity drops below threshold
      ↓
merge short scenes (< min_duration)
      ↓
ffmpeg -segment_times (stream copy)
```

**Pros:**

- Frame-accurate detection regardless of keyframe placement
- Handles heavily compressed or poorly encoded sources

**Cons:**

- Much slower - decodes every frame
- Requires `pip install amverge[edge]` (OpenCV)

---

## Comparison

| | keyframe | edge |
|---|---|---|
| Speed | Fast | Slow |
| Accuracy | Good | Excellent |
| Lossless output | Yes | Yes |
| Extra dependency | None | OpenCV |
| Best for | Anime, broadcast | Heavily compressed / bad encodes |

---

## Tuning

### `--min-duration N`

Merges any scene shorter than N seconds into the next one.  
Default `0.25`. Raise to `0.5` or `1.0` to reduce false cuts.

### `--similarity-threshold N`

Controls what counts as a "similar" pair of adjacent scenes (0.0 - 1.0).  
Lower = stricter. Default `0.10`.  
Similarity pairs are flagged in the output table but not automatically merged - you decide.

### `--edge-threshold N` (edge method only)

Cosine similarity drop that counts as a cut. Default `0.15`.  
Raise to catch subtler cuts; lower to reduce false positives.

### `--edge-radius N` (edge method only)

Window radius around candidate keyframes. Default `0.6`.

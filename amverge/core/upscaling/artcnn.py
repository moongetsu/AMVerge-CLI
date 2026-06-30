import os
import ssl
import subprocess
import threading
import urllib.error
import urllib.request

import numpy as np

from ..infra.config import get_models_dir
from .ffmpeg_helpers import CREATE_NO_WINDOW, build_ffmpeg_pipe, mux_audio
from .registry import QUALITY_PRESETS, get_model


def get_artcnn_dir():
    return os.path.join(get_models_dir(), "artcnn")


def get_artcnn_path(model_key):
    entry = get_model(model_key)
    if entry is None or "file" not in entry:
        raise ValueError(f"Unknown ONNX model: {model_key}")
    return os.path.join(get_artcnn_dir(), entry["file"])


def is_artcnn_downloaded(model_key):
    try:
        return os.path.exists(get_artcnn_path(model_key))
    except ValueError:
        return False


def download_artcnn(model_key, progress_cb=None, retries=3):
    entry = get_model(model_key)
    if entry is None:
        raise ValueError(f"Unknown ONNX model: {model_key}")

    url = entry["url"]
    dest_dir = get_artcnn_dir()
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, entry["file"])
    if os.path.exists(dest):
        return True

    temp_path = dest + ".part"
    ctx = ssl._create_unverified_context()

    for attempt in range(retries):
        try:
            existing = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
            headers = {"User-Agent": "amverge/1.0"}
            if existing > 0 and attempt > 0:
                headers["Range"] = f"bytes={existing}-"
            elif existing > 0:
                os.remove(temp_path)
                existing = 0

            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=120, context=ctx)
            code = resp.getcode()
            if code not in (200, 206):
                raise urllib.error.HTTPError(url, code, "", None, None)

            total = int(resp.headers.get("Content-Length", 0))
            file_mode = "ab" if code == 206 else "wb"
            downloaded = existing if code == 206 else 0
            if code == 206:
                total = existing + total
            chunk_size = 65536

            with open(temp_path, file_mode) as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        pct = min(99, int(downloaded * 100 / total))
                        progress_cb(pct, f"Downloading {model_key}... {pct}%")

            if total > 0 and downloaded != total:
                raise ConnectionError(f"Incomplete: {downloaded}/{total} bytes")

            os.rename(temp_path, dest)
            if progress_cb:
                progress_cb(100, f"Downloaded {model_key}")
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError,
                TimeoutError, OSError) as e:
            if attempt == retries - 1:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                raise RuntimeError(f"Download failed for {model_key}: {e}")
    return False


def upscale_video_artcnn(input_path, output_path, model_key, entry, scale, preset,
                         fit_w, fit_h, progress_cb=None):
    import cv2
    import onnxruntime

    q = QUALITY_PRESETS.get(preset, QUALITY_PRESETS["high"])

    providers = []
    if "CUDAExecutionProvider" in onnxruntime.get_available_providers():
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")

    onnx_path = get_artcnn_path(model_key)
    if not os.path.exists(onnx_path):
        download_artcnn(model_key, progress_cb)

    session = onnxruntime.InferenceSession(onnx_path, providers=providers)
    input_name = session.get_inputs()[0].name

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open: {input_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_val = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    out_w = w * scale
    out_h = h * scale

    extra_vf = None
    if fit_w > 0 and fit_h > 0 and (out_w > fit_w or out_h > fit_h):
        extra_vf = f"scale={fit_w}:{fit_h}:force_original_aspect_ratio=decrease:flags=lanczos"

    ffmpeg_cmd = build_ffmpeg_pipe(out_w, out_h, fps_val, q["crf"], q["x264"],
                                   q.get("tune"), output_path, extra_vf)

    ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=CREATE_NO_WINDOW)

    def _read_stderr():
        try:
            for _ in ffmpeg_proc.stderr:
                pass
        except Exception:
            pass
    threading.Thread(target=_read_stderr, daemon=True).start()

    try:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
            y, u, v = cv2.split(yuv)
            y_f = y.astype(np.float32) / 255.0
            y_tensor = y_f[np.newaxis, np.newaxis, ...]

            outputs = session.run(None, {input_name: y_tensor})
            y_upscaled = outputs[0][0, 0]

            y_out = np.clip(y_upscaled * 255.0, 0, 255).astype(np.uint8)
            u_out = cv2.resize(u, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
            v_out = cv2.resize(v, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)

            yuv_out = cv2.merge([y_out, u_out, v_out])
            result_bgr = cv2.cvtColor(yuv_out, cv2.COLOR_YUV2BGR)

            if ffmpeg_proc.poll() is None:
                try:
                    ffmpeg_proc.stdin.write(result_bgr.tobytes())
                except (BrokenPipeError, OSError):
                    break

            frame_idx += 1
            if progress_cb:
                pct = min(100, int((frame_idx / total_frames) * 100))
                progress_cb(pct, f"ArtCNN upscaling... {frame_idx}/{total_frames}")
    finally:
        cap.release()
        try:
            ffmpeg_proc.stdin.close()
        except Exception:
            pass
        ffmpeg_proc.wait()

    mux_audio(str(output_path), str(input_path))

# Upscale Examples

AI video upscaling with three methods:

- **ML** - ShuffleCUGAN neural network (needs `amverge[upscale]`)
- **Anime4K** - GPU shader-based (FFmpeg only, fastest)
- **ArtCNN** - Lightweight CNN via ONNX Runtime (needs `amverge[upscale]`)

## Requirements

```bash
pip install amverge[upscale]         # for ML and ArtCNN methods
amverge models --download adore      # pre-download ML model
amverge models --download C4F32      # pre-download ArtCNN model
amverge models --download anime4k    # pre-download Anime4K shaders
```

## Examples

| File | What It Does |
|------|-------------|
| `01_ml_upscale.py` | Upscale with ShuffleCUGAN model (adore, 2x) |
| `02_anime4k_upscale.py` | Fast shader-based upscale with Anime4K |
| `03_manage_models.py` | List, download, and delete model files |

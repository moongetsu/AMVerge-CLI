<p align="center">
  <img src="../../assets/AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Similarity Examples

**Detect visually similar adjacent scenes.**  
Compares thumbnail pixel arrays using cosine similarity on 8x8 average-pooled blocks.

---

## How It Works

```txt
scene thumbnails (.jpg)
     ↓
load as RGB pixel arrays
     ↓
average-pool to 8x8 blocks
     ↓
flatten + normalize
     ↓
cosine similarity between adjacent scenes
     ↓
flag pairs below dissimilarity threshold (default 0.10)
```

Lower threshold = stricter. Similarity pairs are flagged for review, not automatically merged.

---

## Examples

| File | Description |
|---|---|
| [01_find_similar.py](01_find_similar.py) | find similar scene pairs from a detect run |

---

## Quick Start

```bash
pip install amverge

# Detect scenes with thumbnails, then check similarity
python examples/similarity/01_find_similar.py episode.mp4
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `check_pair_similar()`, `find_similar_pairs()` |

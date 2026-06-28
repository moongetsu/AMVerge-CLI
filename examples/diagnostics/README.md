<p align="center">
  <img src="../../assets/AMVerge-CLI.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Diagnostics Examples

**GPU info, dependency versions, and environment checks.**  
Equivalent to `amverge gpu` and `amverge version`.

---

## Examples

| File | Description |
|---|---|
| [01_gpu_check.py](01_gpu_check.py) | PyTorch CUDA / GPU / VRAM status |
| [02_version_info.py](02_version_info.py) | all dependency versions |

---

## Quick Start

```bash
pip install amverge[ml,edge,discord]

# GPU check
python examples/diagnostics/01_gpu_check.py

# Version info
python examples/diagnostics/02_version_info.py
```

---

## See Also

| | |
|---|---|
| [CLI Reference](../../docs/cli-reference.md) | `amverge gpu`, `amverge version`, `amverge doctor` |

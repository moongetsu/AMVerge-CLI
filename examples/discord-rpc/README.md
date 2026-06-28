<p align="center">
  <img src="../../assets/amverge_title_gif.gif" alt="AMVerge CLI" width="1440"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/pypi-amverge-22c55e?style=flat-square" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-22c55e?style=flat-square" alt="License"/>
</p>

# Discord RPC Examples

**Live Discord Rich Presence status updates.**  
Shows detection, export, and merge progress under "Playing AMVerge" in Discord.
Uses the same application ID as the AMVerge desktop app.

---

## Requirements

```bash
pip install amverge[discord]
```

---

## Examples

| File | Description |
|---|---|
| [01_basic_rpc.py](01_basic_rpc.py) | connect, update status, disconnect |

---

## Quick Start

```bash
pip install amverge[discord]

# Run with Discord open
python examples/discord-rpc/01_basic_rpc.py
```

---

## See Also

| | |
|---|---|
| [Library API](../../docs/library.md) | `DiscordRPC`, `RPC_AVAILABLE` |

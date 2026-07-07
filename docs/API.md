# C2G API / Usage Reference

> Quick reference for using **C2G** programmatically and from the command line.

## Command Line

- `uv run python -m c2g` — C2G CLI
- `bin/compass_radar.py` — radar health

## Programmatic API

Import `c2g.strategy` and `c2g.bridge` for pitch-to-task workflows.

## Configuration

- Stack: python
- Dependencies: see [`../pyproject.toml`](../pyproject.toml) (Python) or [`../package.json`](../package.json) (TypeScript).
- Environment variables and ports: see workspace `protocols/port-registry.yaml` and root `.env.example`.

## Tests

See [`../README.md`](../README.md) for the test command.

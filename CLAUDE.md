# Release checklist

- Before every release, bump `version` in `pyproject.toml` so it matches the release tag (for example `v1.2.0` -> `1.2.0`).
- Releases publish to PyPI when a GitHub release is published (`.github/workflows/publish.yml`), so merge to `main` first, then tag from `main`.
- `pyproject.toml` uses CRLF line endings; keep them.
- Tests: `pytest`. Lint: `ruff check .`.

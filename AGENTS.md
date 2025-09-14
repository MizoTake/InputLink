# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `src/input_link/` with subpackages: `apps/` (CLI/GUI entry), `core/` (input, control, logging), `gui/` (PySide6 UI), `models/` (Pydantic configs), `network/` (WebSocket), `virtual/` (OS adapters).
- Entrypoints: console scripts `input-link-sender`, `input-link-receiver`; CLI aggregator `main.py`.
- Tests in `tests/` (`unit/`, `integration/`, `e2e/`). Docs in `docs/`. Build helpers in `build/` (`build.sh`, `build.bat`).

## Build, Test, and Development Commands
- `make install-dev` — editable install with dev/test/build extras.
- `make test` / `make test-cov` — run pytest; `test-cov` also writes HTML coverage.
- `make lint` — `ruff` (src/tests) then `mypy --strict` (src).
- `make format` — `black` + `isort` over `src` and `tests`.
- Run apps: `make run-sender`, `make run-receiver`, `make run-gui`.
- Examples: `python -m input_link.apps.sender --host 127.0.0.1 --port 8765`, `python main.py receiver --port 9000`.

## Coding Style & Naming Conventions
- Python ≥ 3.8; 4‑space indentation; add type hints for new/changed code.
- Formatting: `black` (line length 100) and `isort` (profile=black).
- Linting: `ruff`; Typing: `mypy --strict`.
- Names: packages/modules `snake_case`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest` with markers: `unit`, `integration`, `e2e`, `asyncio`, `slow`.
- Discovery: files `test_*.py`, classes `Test*`, functions `test_*`.
- Run subsets: `pytest -m unit` or `pytest tests/integration -v`.
- Prefer fast unit tests; isolate I/O via fakes/mocks; use `pytest-asyncio` for async code.

## Commit & Pull Request Guidelines
- Conventional Commits. Scopes: `core|network|gui|virtual|apps|models|tests|docs`.
- Examples: `feat(network): add reconnect backoff`, `fix(gui): prevent freeze on close`.
- PRs include what/why, linked issues, and a test plan; add screenshots/GIFs for GUI changes.
- Ensure CI passes: at minimum `make lint && make test` (or `make check` if available).

## Security & Configuration Tips
- Windows-only virtual gamepad uses `vgamepad`; GUI requires `PySide6`. Install via `make install-dev`.
- Keep secrets out of VCS. Use `src/input_link/models/config.py`; pass configs with `--config <path>` when supported.


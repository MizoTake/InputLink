# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `src/input_link/` with subpackages: `apps/` (CLI/GUI entry modules), `core/` (input, control, logging), `gui/` (PySide6 UI), `models/` (Pydantic configs), `network/` (WebSocket client/server), and `virtual/` (OS adapters).
- Tests are under `tests/` (`unit/`, `integration/`, `e2e/`). Docs are in `docs/` (architecture, development, testing, user-guide).
- Entrypoints: console scripts `input-link-sender`, `input-link-receiver`; CLI aggregator `main.py`. Build helpers in `build/` (`build.bat`, `build.sh`).

## Build, Test, and Development Commands
- `make install-dev` — editable install with dev/test/build extras.
- `make test` | `make test-cov` — run pytest (optionally with coverage HTML).
- `make lint` — `ruff` (src/tests) then `mypy` (strict on `src`).
- `make format` — `black` + `isort` over `src` and `tests`.
- Run apps: `make run-sender`, `make run-receiver`, `make run-gui`.
- Examples: `python -m input_link.apps.sender --host 127.0.0.1 --port 8765`, `python main.py receiver --port 9000`.

## Coding Style & Naming Conventions
- Python ≥3.8. Format with `black` (line length 100) and `isort` (profile=black). Lint with `ruff`. Type-check with `mypy --strict`.
- Indentation: 4 spaces. Add type hints for new/changed code.
- Names: packages/modules `snake_case`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest` with markers (`unit`, `integration`, `e2e`, `asyncio`, `slow`). Discovery: files `test_*.py`, classes `Test*`, functions `test_*`.
- Run subsets: `pytest -m unit`, `pytest tests/integration -v`. Use `make test-cov` to check coverage for touched paths.
- Prefer fast unit tests; isolate I/O via fakes/mocks. For async, use `pytest-asyncio`.

## Commit & Pull Request Guidelines
- Use Conventional Commits. Examples: `feat(network): add reconnect backoff`, `fix(gui): prevent freeze on close`, `test(core): cover rate limiter`.
- Scopes: `core|network|gui|virtual|apps|models|tests|docs`.
- PRs include: what/why, linked issues, test plan; add screenshots/GIFs for GUI changes. Ensure `make check` (lint + test) passes.

## Security & Configuration Tips
- Windows-only virtual gamepad uses `vgamepad`; GUI requires `PySide6`. Install via `make install-dev`.
- Keep secrets out of VCS. Use config files (see `src/input_link/models/config.py`) and pass with `--config <path>` when supported.


# Repository Guidelines

## Project Structure & Module Organization
- Source code lives in `src/input_link/` with subpackages: `core/` (logic, I/O), `network/` (WebSocket client/server), `gui/` (PySide6 UI), `apps/` (CLI/GUI entry modules), `virtual/` (platform adapters), and `models/` (Pydantic configs, data models).
- Tests are in `tests/`: `tests/unit/` for fast logic tests, `tests/integration/` for end‑to‑end flows.
- Entry points: `main.py` (CLI group) and console scripts `input-link-sender` and `input-link-receiver`.

## Build, Test, and Development Commands
- `make install-dev` — Install package with dev/test/build extras.
- `make test` / `make test-cov` — Run pytest (with or without coverage HTML report).
- `make lint` — Run `ruff` on `src` and `tests`, then `mypy` on `src`.
- `make format` — Apply `black` and `isort` to `src` and `tests`.
- `make run-sender` / `make run-receiver` / `make run-gui` — Launch apps locally.
- Examples: `python main.py sender --host 127.0.0.1 --port 8765`, `python -m input_link.apps.gui_main`.

## Coding Style & Naming Conventions
- Formatting: `black` (line length 100) and `isort` (profile=black). Linting via `ruff`. Static typing is enforced with `mypy --strict`.
- Indentation: 4 spaces. Typing: add type hints to public functions and new code.
- Naming: packages/modules `snake_case`, classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest` with markers (`unit`, `integration`, `asyncio`, etc.). Test discovery: files `test_*.py`, classes `Test*`, functions `test_*`.
- Run subsets: `pytest -m unit`, `pytest tests/integration -v`.
- Aim for meaningful coverage on changed paths; use `make test-cov` to verify.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat/core: …`, `fix/network: …`, `docs: …`, `test: …`. Prefer scopes from: `core|network|gui|virtual|apps|tests|models`.
- Commits: imperative mood, concise subject, helpful body for nontrivial changes.
- PRs: include what/why, linked issues, test plan, and screenshots for GUI changes. Keep diffs focused.

## Security & Configuration Tips
- Windows-only dependency `vgamepad` powers virtual controllers; GUI requires `PySide6`. Install via `make install-dev`.
- Use `--config <path>` with sender/receiver to load settings. Do not commit secrets; prefer local config files ignored by VCS.


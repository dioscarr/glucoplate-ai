# Lessons from `basic-init`

The `basic-init` branch was used to get a basic runtime working in the real development environment. It exposed several lessons that should shape the project going forward.

## 1. Runtime integration must be verified, not assumed

The first implementation followed the intended Copilot SDK direction but assumed several SDK/runtime details. The branch proved that the application needs a small smoke-test script and a runtime wrapper that can diagnose environment problems.

Added:

- `scripts/check_copilot.py`
- CLI path discovery
- default model fallback
- safer session cleanup

## 2. Codespaces has specific Copilot runtime behavior

The Copilot CLI may not be available through a normal PATH lookup. The app now checks common locations including the VS Code remote extension storage path.

## 3. Let the runtime choose the default model first

Hard-coding a model too early creates unnecessary failures. The client now accepts `model=None` so the Copilot runtime can choose a supported default.

## 4. Logging is part of architecture

Without request logging and centralized app logging, debugging API, UI, and agent behavior is too slow.

Added:

- `app/logging_config.py`
- request timing middleware
- `loguru` dependency

## 5. Keep the UI deployable first

The project should keep a simple static UI served by FastAPI before adding a larger frontend framework. This keeps the first deployment path easy.

## 6. Main branch should absorb proven branch fixes selectively

`basic-init` diverged from `main`. Instead of blindly merging, the proven fixes were applied selectively while preserving newer architecture work such as:

- multi-agent orchestration
- store and product APIs
- `app/web` UI structure

## Follow-up work

- Add CI step for `scripts/check_copilot.py` as optional/non-blocking.
- Add health endpoint for AI runtime diagnostics.
- Add structured error metadata when falling back from Copilot to local generation.
- Add environment documentation for GitHub Codespaces.

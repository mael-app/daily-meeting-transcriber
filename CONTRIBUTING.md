# Contributing

Contributions are welcome. Please follow the guidelines below to keep the codebase consistent.

## Getting started

```bash
git clone https://github.com/mael-app/daily-meeting-transcriber.git
cd daily-meeting-transcriber
pip install -r requirements.txt
cp .env.example .env  # fill in your values
```

## Workflow

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes.
3. Test locally before opening a PR:
   ```bash
   python -m uvicorn app:app --reload --port 8080
   curl -X POST "http://localhost:8080/process-audio" -F "file=@meeting.m4a"
   ```
4. Open a pull request against `main` with a clear description of what and why.

## Guidelines

- **One concern per PR** — keep changes focused and reviewable.
- **No dead code** — remove unused imports, functions, and variables.
- **English only** — all code, comments, and commit messages must be in English.
- **No hardcoded secrets or configuration** — use environment variables and `AppConfig`.
- **Follow existing patterns** — HTTP calls use `urllib.request`, logging uses `loguru`, config is centralized in `utils/config.py`.

## Commit messages

Use the conventional commits format:

```
feat: add support for speaker diarization
fix: handle empty transcript from Whisper
chore: update dependencies
docs: document PROMPT_CONFIG format
```

## Reporting issues

Open an issue with a clear title, steps to reproduce, and the relevant logs or error messages.

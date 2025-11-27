# 🎤 Daily Meeting Transcriber

A modern API and CLI tool to transcribe and summarize your daily meetings using OpenAI Whisper and GPT-4o mini, with optional Notion integration.

---

## Features

- 🎧 Audio transcription (Whisper, supports mp3, m4a, wav, etc.)
- 🤖 AI-powered structured summary generation (GPT-4o mini)
- 📦 Notion integration: send summaries to your Notion database (optional)
- 📝 Markdown output
- 🌍 Multilingual (default: French)
- 🪄 FastAPI HTTP API (with OpenAPI docs)
- 🐳 Docker-ready, deployable to Google Cloud Run
- 📊 Token usage tracking
- 🦄 Colorful logging with Loguru

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/mael-app/daily-meeting-transcriber.git
cd daily-meeting-transcriber
pip install -r requirements.txt
```

### 2. Set Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `NOTION_TOKEN` (optional): Notion integration token
- `NOTION_DB_SCHEMA` (optional): Notion DB schema (JSON)
- `NOTION_CATEGORY`, `NOTION_TITLE` (optional): Notion config
- `PROMPT_FILE` (optional): Custom prompt file (default: `prompt.json`)

Example:
```bash
export OPENAI_API_KEY=sk-...
```

### 3. Run with Docker

```bash
docker build -t daily-meeting-transcriber .
docker run -e OPENAI_API_KEY=sk-... -p 8080:8080 daily-meeting-transcriber
```

### 4. API Usage

- Open [http://localhost:8080/docs](http://localhost:8080/docs) for interactive docs.
- Main endpoint: `POST /process-audio`
    - `file`: audio file (required)
    - `notion_schema`: Notion DB schema (JSON, optional)

Example with `curl`:
```bash
curl -X POST "http://localhost:8080/process-audio" \
  -F "file=@meeting.m4a"
```

Send a request to the transcript endpoint:

```bash
curl -X POST \
  -F "audio_file=@recording.m4a" \
  http://localhost:8080/transcript
```

If you want to provide a custom Notion DB schema, set the NOTION_DB_SCHEMA environment variable to a valid JSON string representing your Notion database schema.

## Notion DB Schema Format

The Notion DB schema should be provided as a JSON string in the `NOTION_DB_SCHEMA` environment variable. Example:

```
export NOTION_DB_SCHEMA='{"properties": {"Name": {"title": {}}, "Category": {"select": {}}}}'
```

### 5. CLI Usage (Python)

You can also use the core logic in your own scripts by importing the services in `services/`.

---

## Project Structure

- `app.py` — FastAPI entrypoint
- `services/` — Core logic (transcription, summary, Notion, audio)
- `utils/` — Config, env, helpers
- `requirements.txt` — Python dependencies
- `Dockerfile` — Production-ready Docker build

---

## Configuration

- All environment variables are loaded via `utils/env.py` (use `get_env()`)
- Custom prompts: put a `prompt.json` file at the root, or set `PROMPT_FILE`
- Notion integration: pass a Notion DB schema as a file to the API, or set `NOTION_JSON`

---

## Logging

- Uses [Loguru](https://github.com/Delgan/loguru) for colorful, structured logs
- All logs are in English for consistency

---

## Deployment

- Dockerfile is multi-stage and production-ready
- Designed for Google Cloud Run (single worker, port 8080)
- See `.github/workflows/docker-publish.yml` for CI/CD to GitHub Container Registry

---

## License

MIT

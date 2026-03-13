# 🎤 Daily Meeting Transcriber

A FastAPI service to transcribe and summarize your daily meetings using OpenAI Whisper and GPT-4o mini, with optional Notion integration.

---

## Features

- 🎧 Audio transcription via OpenAI Whisper (mp3, m4a, wav, and any format supported by ffmpeg)
- 🤖 Structured Markdown summary generation via GPT-4o mini
- 📦 Optional Notion integration: automatically publish summaries to your Notion database
- 🌍 Multilingual — language is configurable via `PROMPT_CONFIG`
- 🪄 FastAPI HTTP API with interactive OpenAPI docs at `/docs`
- 📊 Token usage tracking in every response
- 🦄 Structured logging with Loguru

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/mael-app/daily-meeting-transcriber.git
cd daily-meeting-transcriber
pip install -r requirements.txt
```

> ffmpeg must be installed on your system for audio processing (`brew install ffmpeg` / `apt install ffmpeg`).

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | API key for your OpenAI-compatible platform |
| `PROMPT_CONFIG` | Yes | Prompts as a JSON string (see [Custom Prompts](#custom-prompts)) |
| `NOTION_TOKEN` | No | Notion integration token |
| `NOTION_DB_SCHEMA` | No* | Notion database schema as a JSON string |
| `NOTION_TITLE` | No | Title for created Notion pages (default: `Daily`) |
| `NOTION_CATEGORY` | No | Category select value for Notion pages (default: `Standup`) |
| `OPENAI_WHISPER_ENDPOINT` | No | Whisper-compatible transcription endpoint (default: OpenAI) |
| `OPENAI_CHAT_ENDPOINT` | No | Chat completions endpoint (default: OpenAI) |
| `WHISPER_MODEL` | No | Transcription model (default: `whisper-1`) |
| `CHAT_MODEL` | No | Chat model (default: `gpt-4o-mini`) |

*Required only if `NOTION_TOKEN` is set and no schema is uploaded per-request.

### 3. Run locally

```bash
# With hot reload
python -m uvicorn app:app --reload --port 8080

# Or with Docker Compose (loads .env automatically)
docker-compose up --build
```

### 4. API Usage

Open [http://localhost:8080/docs](http://localhost:8080/docs) for interactive documentation.

**Endpoints:**

- `GET /health` — Healthcheck
- `POST /process-audio` — Transcribe and summarize an audio file

**Example:**

```bash
curl -X POST "http://localhost:8080/process-audio" \
  -F "file=@meeting.m4a"
```

**Response:**

```json
{
  "tokens": 1234,
  "transcript_success": true,
  "markdown": "### Work from yesterday\n- ...",
  "notion_sent": false
}
```

---

## Notion Integration

To enable Notion publishing, set `NOTION_TOKEN` and `NOTION_DB_SCHEMA`.

If `NOTION_TOKEN` is not set, Notion is skipped entirely and the response still contains the transcript and summary.

### 1. Create a Notion integration

Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations), create a new integration, and copy the **Internal Integration Token** — this is your `NOTION_TOKEN`.

### 2. Get your database ID

Open your Notion database in the browser. The URL looks like:

```
https://www.notion.so/yourworkspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...
```

The 32-character string before the `?` is your database ID.

Alternatively, use the Notion API to retrieve it:

```bash
curl -X GET "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer secret_..." \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"filter": {"value": "database", "property": "object"}}'
```

Look for the `"id"` field in the response matching your database.

### 3. Connect the integration to your database

In Notion, open the database → click `...` (top right) → **Connections** → add your integration.

### 4. Set the environment variables

```bash
export NOTION_TOKEN="secret_..."
export NOTION_DB_SCHEMA='{"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}'
```

The `NOTION_DB_SCHEMA` value only needs to contain the `id` (or `database_id`) key. The service reads that field to identify the target database.

You can also upload the schema per-request via the optional `notion_schema` field:

```bash
curl -X POST "http://localhost:8080/process-audio" \
  -F "file=@meeting.m4a" \
  -F "notion_schema=@schema.json"
```

---

## Custom Prompts

`PROMPT_CONFIG` is required. Set it to a JSON string containing your prompts:

```bash
export PROMPT_CONFIG='{
  "system_prompt": "You are an assistant that summarizes developer standups.",
  "user_prompt": "Summarize the following transcript:\n---\n{transcript}\n---",
  "language": "en"
}'
```

The `{transcript}` placeholder is required in `user_prompt`. The `language` value is passed directly to the Whisper API.

On Kubernetes, use a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: transcriber-config
data:
  PROMPT_CONFIG: |
    {"system_prompt": "...", "user_prompt": "...\n---\n{transcript}\n---", "language": "en"}
```

---

## OpenAI-compatible platforms

`OPENAI_API_KEY`, `OPENAI_WHISPER_ENDPOINT`, and `OPENAI_CHAT_ENDPOINT` work with any platform that exposes an OpenAI-compatible API — Azure OpenAI, Together AI, local inference servers, etc.

Example with a local server:

```bash
OPENAI_API_KEY="local"
OPENAI_WHISPER_ENDPOINT="http://localhost:8000/v1/audio/transcriptions"
OPENAI_CHAT_ENDPOINT="http://localhost:8000/v1/chat/completions"
WHISPER_MODEL="whisper-large-v3"
CHAT_MODEL="llama-3.1-8b-instruct"
```

---

## Project Structure

```
app.py              FastAPI entrypoint
services/
  audio_service.py      Request orchestrator
  transcription_service.py  Whisper API integration
  summary_service.py    GPT-4o mini integration
  notion_service.py     Notion API integration
utils/
  config.py         App configuration loader
  env.py            Environment variable helper
```

---

## Deployment

The CI/CD pipeline (`.github/workflows/docker-publish.yml`) builds a multi-arch Docker image (`linux/amd64`, `linux/arm64`) and pushes it to GitHub Container Registry (`ghcr.io`) on every push to `main`.

---

## License

MIT

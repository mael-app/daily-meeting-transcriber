from fastapi import UploadFile
from fastapi.responses import JSONResponse
from services.transcription_service import transcribe_audio
from services.summary_service import generate_summary_with_prompts
from services.notion_service import send_to_notion
from utils.config import AppConfig
from utils.env import get_env
import os
import tempfile
import json
from typing import Optional


def _build_response(tokens, transcript, summary, notion_sent=False, error=None):
    data = {
        "tokens": tokens,
        "transcript_success": bool(transcript),
        "markdown": summary,
        "notion_sent": notion_sent,
    }
    if error is not None:
        data["error"] = error
    return JSONResponse(data)


def process_audio_service(file: UploadFile, notion_schema: Optional[UploadFile]):
    api_key = get_env("OPENAI_API_KEY", required=True)

    audio_bytes = file.file.read()
    with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(file.filename)[-1] or ".wav") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        transcript = transcribe_audio(tmp.name, api_key)

    system_prompt = AppConfig.custom_system
    user_prompt_template = AppConfig.custom_user

    summary, tokens = generate_summary_with_prompts(
        transcript,
        api_key,
        system_prompt,
        user_prompt_template
    )

    notion_token = get_env("NOTION_TOKEN", default=None)
    if not notion_token:
        return _build_response(tokens, transcript, summary)

    notion_schema_dict = None
    if notion_schema is not None:
        try:
            notion_schema_bytes = notion_schema.file.read()
            notion_schema_dict = json.loads(notion_schema_bytes.decode("utf-8"))
        except Exception as e:
            return _build_response(tokens, transcript, summary, error=f"Invalid Notion schema file: {e}")
    else:
        notion_db_schema_env = get_env("NOTION_DB_SCHEMA", default=None)
        if not notion_db_schema_env:
            return _build_response(tokens, transcript, summary, error="NOTION_DB_SCHEMA is not configured")
        try:
            notion_schema_dict = json.loads(notion_db_schema_env)
        except Exception as e:
            return _build_response(tokens, transcript, summary, error=f"Invalid NOTION_DB_SCHEMA value: {e}")

    db_id = notion_schema_dict.get("id") or notion_schema_dict.get("database_id")
    if not db_id:
        return _build_response(
            tokens, transcript, summary,
            error="Notion DB id not found in schema. Key 'id' or 'database_id' missing."
        )

    page_title = AppConfig.notion_title or None
    category = AppConfig.notion_category or None
    try:
        send_to_notion(summary, notion_token, db_id, category, page_title)
        return _build_response(tokens, transcript, summary, notion_sent=True)
    except Exception as e:
        return _build_response(tokens, transcript, summary, error=f"Notion send failed: {e}")

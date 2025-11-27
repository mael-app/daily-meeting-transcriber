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


def process_audio_service(file: UploadFile, notion_schema: Optional[UploadFile]):
    api_key = get_env("OPENAI_API_KEY", required=True)
    audio_bytes = file.file.read()
    with tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(file.filename)[-1] or ".wav") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        transcript = transcribe_audio(tmp.name, api_key)
    # Prompt strings intentionally left in French as per user request
    system_prompt = AppConfig.custom_system if AppConfig.custom_system else "Tu es un assistant chargé de générer un résumé structuré en Markdown d'un compte rendu de daily meeting de développeurs."
    user_prompt_template = AppConfig.custom_user if AppConfig.custom_user else """Analyse le texte fourni, identifie les sujets discutés, les tâches réalisées, les plans de la journée, les points techniques, les blocages éventuels et les actions à suivre.\n\nSuis strictement le format suivant :\n\n### Travail d'hier\n- Liste concise des réalisations de la veille.\n\n### Organisation de la journée\n- Liste des réunions, priorités ou tâches prévues aujourd'hui.\n\n### Revues de code\n- Liste des PR à reviewer ou en attente.\n\n### Points techniques discutés\n- Liste des problèmes, propositions ou réflexions techniques soulevées.\n\n### Action Items\n- Liste à cocher [ ] des prochaines actions identifiées.\n\nRègles :\n- Utilise un ton professionnel et factuel.\n- Ne garde aucune phrase inutile, blague ou digression.\n- Résume de manière claire et synthétique (max 10 lignes par section).\n- Corrige la grammaire et les formulations orales.\n- Si une section n'a aucun contenu, ne l'affiche pas.\n\nTranscript du daily meeting :\n---\n{transcript}\n---"""
    summary, tokens = generate_summary_with_prompts(
        transcript,
        api_key,
        system_prompt,
        user_prompt_template
    )
    notion_sent = False
    notion_schema_dict = None
    if notion_schema is not None:
        try:
            notion_schema_bytes = notion_schema.file.read()
            notion_schema_dict = json.loads(notion_schema_bytes.decode("utf-8"))
        except Exception as e:
            return JSONResponse({
                "tokens": tokens,
                "transcript_success": transcript is not None and len(transcript) > 0,
                "markdown": summary,
                "notion_sent": False,
                "error": f"Invalid Notion schema file: {e}"
            })
    elif AppConfig.notion_json:
        try:
            with open(AppConfig.notion_json, 'r', encoding='utf-8') as f:
                notion_schema_dict = json.load(f)
        except Exception as e:
            return JSONResponse({
                "tokens": tokens,
                "transcript_success": transcript is not None and len(transcript) > 0,
                "markdown": summary,
                "notion_sent": False,
                "error": f"Notion schema file error: {e}"
            })
    if notion_schema_dict:
        db_id = notion_schema_dict.get('id') or notion_schema_dict.get('database_id')
        if db_id:
            notion_token = get_env('NOTION_TOKEN', default=None)
            page_title = AppConfig.notion_title if AppConfig.notion_title else None
            category = AppConfig.notion_category if AppConfig.notion_category else None
            try:
                send_to_notion(summary, notion_token, db_id, category, page_title)
                notion_sent = True
            except Exception as e:
                return JSONResponse({
                    "tokens": tokens,
                    "transcript_success": transcript is not None and len(transcript) > 0,
                    "markdown": summary,
                    "notion_sent": False,
                    "error": f"Notion send failed: {e}"
                })
        else:
            return JSONResponse({
                "tokens": tokens,
                "transcript_success": transcript is not None and len(transcript) > 0,
                "markdown": summary,
                "notion_sent": False,
                "error": "Notion DB id not found in schema. Key 'id' or 'database_id' missing."
            })
    return JSONResponse({
        "tokens": tokens,
        "transcript_success": transcript is not None and len(transcript) > 0,
        "markdown": summary,
        "notion_sent": notion_sent
    })

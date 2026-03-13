import json
from utils.env import get_env


class AppConfig:
    # Notion
    notion_category = get_env('NOTION_CATEGORY', default=None)
    notion_title = get_env('NOTION_TITLE', default=None)

    # Prompts
    custom_system: str
    custom_user: str
    custom_language: str = "en"

    # API endpoints (overridable for OpenAI-compatible platforms)
    openai_whisper_endpoint = get_env('OPENAI_WHISPER_ENDPOINT', default="https://api.openai.com/v1/audio/transcriptions")
    openai_chat_endpoint = get_env('OPENAI_CHAT_ENDPOINT', default="https://api.openai.com/v1/chat/completions")
    notion_api_url = "https://api.notion.com/v1/pages"

    # Models (overridable)
    whisper_model = get_env('WHISPER_MODEL', default="whisper-1")
    chat_model = get_env('CHAT_MODEL', default="gpt-4o-mini")


_prompt_config_raw = get_env('PROMPT_CONFIG', required=True)
try:
    _prompts = json.loads(_prompt_config_raw)
except json.JSONDecodeError as e:
    raise ValueError(f"PROMPT_CONFIG is not valid JSON: {e}") from e

if not _prompts.get('system_prompt') or not _prompts.get('user_prompt'):
    raise ValueError("PROMPT_CONFIG must contain 'system_prompt' and 'user_prompt' keys")

AppConfig.custom_system = _prompts['system_prompt']
AppConfig.custom_user = _prompts['user_prompt']
if _prompts.get('language'):
    AppConfig.custom_language = _prompts['language']

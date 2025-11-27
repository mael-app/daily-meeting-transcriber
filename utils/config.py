import os
import json
from utils.env import get_env


class AppConfig:
    notion_json = get_env('NOTION_JSON', default=None)
    notion_category = get_env('NOTION_CATEGORY', default=None)
    notion_title = get_env('NOTION_TITLE', default=None)
    prompt_file = get_env('PROMPT_FILE', default='prompt.json')
    custom_system = None
    custom_user = None
    custom_language = None


# Load custom prompts if present
if os.path.exists(AppConfig.prompt_file):
    try:
        with open(AppConfig.prompt_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            AppConfig.custom_system = prompts.get('system_prompt')
            AppConfig.custom_user = prompts.get('user_prompt')
            AppConfig.custom_language = prompts.get('language')
    except (OSError, json.JSONDecodeError) as e:
        # Log or ignore specific errors (file not found, decode error)
        pass

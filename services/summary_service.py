import json
import urllib.request
import urllib.error
import socket
import time
from loguru import logger
from utils.config import AppConfig


def generate_summary_with_prompts(transcript: str, api_key: str, system_prompt: str, user_prompt_template: str):
    """Generates a structured Markdown summary from a transcript."""
    logger.info("\U0001F916 Generating structured summary...")
    user_prompt = user_prompt_template.format(transcript=transcript)
    payload = {
        "model": AppConfig.chat_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    try:
        request = urllib.request.Request(
            AppConfig.openai_chat_endpoint,
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )
        start_time = time.time()
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode())
            summary = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            elapsed_time = time.time() - start_time
            logger.success(f"✅ Summary generated in {elapsed_time:.1f}s")
            logger.info(f"📊 Tokens used: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")
            return summary, total_tokens
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 401:
            logger.error("❌ Error: Invalid OpenAI API key (401 Unauthorized)")
        elif e.code == 429:
            logger.error("❌ Error: Rate limit exceeded or quota reached (429)")
        else:
            logger.error(f"❌ OpenAI API error ({e.code}): {error_body}")
        return "", 0
    except socket.timeout:
        logger.error("❌ Network timeout while generating summary (increase timeout or check connectivity)")
        return "", 0
    except urllib.error.URLError as e:
        logger.error(f"❌ Network error: {e.reason}")
        return "", 0
    except Exception as e:
        logger.error(f"❌ Unexpected error during summary generation: {e}")
        return "", 0

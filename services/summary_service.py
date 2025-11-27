import json
import urllib.request
import urllib.error
import time
import socket
from loguru import logger

OPENAI_CHAT_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def generate_summary_with_prompts(transcript: str, api_key: str, system_prompt: str, user_prompt_template: str):
    """Generates a structured Markdown summary from a transcript."""
    logger.info("\U0001F916 Generating structured summary...")
    user_prompt = user_prompt_template.format(transcript=transcript)
    payload = {
        "model": "gpt-4o-mini",
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
            OPENAI_CHAT_ENDPOINT,
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )
        start_time = time.time()
        logger.info("⏱️  Generating summary...")
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
            logger.info(f"⏱️  Generating: {elapsed_time:.1f}s")
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


def generate_summary(transcript: str, api_key: str):
    """Wrapper with default prompts."""
    system_prompt = "You are an assistant tasked with generating a structured Markdown summary of a developer daily meeting report."
    user_prompt_template = """Analyze the provided text, identify the topics discussed, the tasks completed, the plans for the day, the technical points, any potential blockers, and the follow-up actions.\n\nStrictly follow the format below:\n\n### Work from yesterday\n- Concise list of yesterday's achievements.\n\n### Today's organization\n- List of meetings, priorities, or tasks planned for today.\n\n### Code reviews\n- List of PRs to review or pending.\n\n### Technical points discussed\n- List of problems, proposals, or technical reflections raised.\n\n### Action Items\n- Checklist [ ] of the next identified actions.\n\nRules:\n- Use a professional and factual tone.\n- Do not keep any useless phrases, jokes, or digressions.\n- Summarize clearly and succinctly (max 10 lines per section).\n- Correct grammar and spoken formulations.\n- If a section has no content, do not display it.\n\nTranscript of the daily meeting:\n---\n{transcript}\n---"""
    return generate_summary_with_prompts(transcript, api_key, system_prompt, user_prompt_template)

import json
import urllib.request
import urllib.error
import time
import socket
from loguru import logger

OPENAI_CHAT_ENDPOINT = "https://api.openai.com/v1/chat/completions"


def generate_summary_with_prompts(transcript: str, api_key: str, system_prompt: str, user_prompt_template: str):
    """Génère un résumé structuré en Markdown à partir d'un transcript."""
    logger.info("🤖 Generating structured summary...")
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
        exit(1)
    except socket.timeout:
        logger.error("❌ Network timeout while generating the summary (increase timeout or check connectivity)")
        exit(1)
    except urllib.error.URLError as e:
        logger.error(f"❌ Network error: {e.reason}")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during summary generation: {e}")
        exit(1)


def generate_summary(transcript: str, api_key: str):
    """Wrapper avec prompts par défaut."""
    system_prompt = "Tu es un assistant chargé de générer un résumé structuré en Markdown d'un compte rendu de daily meeting de développeurs."
    user_prompt_template = """Analyse le texte fourni, identifie les sujets discutés, les tâches réalisées, les plans de la journée, les points techniques, les blocages éventuels et les actions à suivre.\n\nSuis strictement le format suivant :\n\n### Travail d'hier\n- Liste concise des réalisations de la veille.\n\n### Organisation de la journée\n- Liste des réunions, priorités ou tâches prévues aujourd'hui.\n\n### Revues de code\n- Liste des PR à reviewer ou en attente.\n\n### Points techniques discutés\n- Liste des problèmes, propositions ou réflexions techniques soulevées.\n\n### Action Items\n- Liste à cocher [ ] des prochaines actions identifiées.\n\nRègles :\n- Utilise un ton professionnel et factuel.\n- Ne garde aucune phrase inutile, blague ou digression.\n- Résume de manière claire et synthétique (max 10 lignes par section).\n- Corrige la grammaire et les formulations orales.\n- Si une section n'a aucun contenu, ne l'affiche pas.\n\nTranscript du daily meeting :\n---\n{transcript}\n---"""
    return generate_summary_with_prompts(transcript, api_key, system_prompt, user_prompt_template)

#!/usr/bin/env python3

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error
import socket
from threading import Event, Thread

OUTPUT_FILENAME_PATTERN = "Daily-{day}-{month}-{year}.md"
DEFAULT_LANGUAGE = "fr"

API_BASE_URL = "https://api.openai.com/v1"
WHISPER_ENDPOINT = f"{API_BASE_URL}/audio/transcriptions"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat/completions"

SYSTEM_PROMPT = "Tu es un assistant chargé de générer un résumé structuré en Markdown d'un compte rendu de daily meeting de développeurs."

USER_PROMPT_TEMPLATE = """Analyse le texte fourni, identifie les sujets discutés, les tâches réalisées, les plans de la journée, les points techniques, les blocages éventuels et les actions à suivre.

Suis strictement le format suivant :

### Travail d'hier
- Liste concise des réalisations de la veille.

### Organisation de la journée
- Liste des réunions, priorités ou tâches prévues aujourd'hui.

### Revues de code
- Liste des PR à reviewer ou en attente.

### Points techniques discutés
- Liste des problèmes, propositions ou réflexions techniques soulevées.

### Action Items
- Liste à cocher [ ] des prochaines actions identifiées.

Règles :
- Utilise un ton professionnel et factuel.
- Ne garde aucune phrase inutile, blague ou digression.
- Résume de manière claire et synthétique (max 10 lignes par section).
- Corrige la grammaire et les formulations orales.
- Si une section n'a aucun contenu, ne l'affiche pas.

Transcript du daily meeting :
---
{transcript}
---"""


def _start_live_timer(label: str):
    """Start a background timer printing elapsed seconds on the same line.

    Args:
        label: Short label displayed before the timer.

    Returns:
        Tuple[threading.Event, threading.Thread]: A stop event to terminate the timer
        and the background thread instance.

    Raises:
        None
    """
    stop_event = Event()

    def _runner():
        start = time.time()
        print(f"\r⏱️  {label}: 0s", end="", flush=True)
        while not stop_event.is_set():
            elapsed = time.time() - start
            print(f"\r⏱️  {label}: {int(elapsed)}s", end="", flush=True)
            time.sleep(0.5)
        elapsed = time.time() - start
        print(f"\r⏱️  {label}: {elapsed:.1f}s")

    t = Thread(target=_runner, daemon=True)
    t.start()
    return stop_event, t


def create_multipart_form_data(fields, files):
    """Build a multipart/form-data HTTP body.

    Args:
        fields: Mapping of field name to value for simple form fields.
        files: Mapping of field name to a tuple (filename, content_bytes, content_type).

    Returns:
        Tuple[str, bytes]: The boundary string and the encoded multipart body.

    Raises:
        None
    """
    boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
    body = []
    
    for key, value in fields.items():
        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        body.append(b'')
        body.append(str(value).encode())
    
    for key, (filename, content, content_type) in files.items():
        body.append(f'--{boundary}'.encode())
        body.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode())
        body.append(f'Content-Type: {content_type}'.encode())
        body.append(b'')
        body.append(content)
    
    body.append(f'--{boundary}--'.encode())
    body.append(b'')
    
    return boundary, b'\r\n'.join(body)


def transcribe_audio(audio_path, api_key, language=DEFAULT_LANGUAGE):
    """Transcribe an audio file using OpenAI Whisper API.

    Args:
        audio_path: Path to the input audio file.
        api_key: OpenAI API key used for authentication.
        language: Language code hint for transcription (e.g., 'fr').

    Returns:
        str: The transcribed text.

    Raises:
        SystemExit: If the audio file cannot be read, the API returns an error,
            a network error occurs, or a timeout happens.
    """
    print(f"🎤 Starting audio transcription (language: {language})...")
    
    try:
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Audio file not found: {audio_path}")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Error: Permission denied reading file: {audio_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        sys.exit(1)
    
    try:
        file_size = os.path.getsize(audio_path)
        size_mb = file_size / (1024 * 1024)
        print(f"📦 Audio size: {size_mb:.1f} MB")
        if size_mb > 24:
            print("⚠️  Heads-up: large file upload. Direct uploads > ~25MB can be slow or fail; consider compressing or trimming.")
    except Exception:
        pass
    
    filename = os.path.basename(audio_path)
    ext = Path(audio_path).suffix.lower()
    if ext == '.mp3':
        content_type = 'audio/mpeg'
    elif ext in ('.m4a', '.mp4'):
        content_type = 'audio/mp4'
    elif ext == '.wav':
        content_type = 'audio/wav'
    else:
        content_type = 'application/octet-stream'
    
    boundary, body = create_multipart_form_data(
        fields={'model': 'whisper-1', 'language': language},
        files={'file': (filename, audio_content, content_type)}
    )
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
    
    try:
        request = urllib.request.Request(
            WHISPER_ENDPOINT,
            data=body,
            headers=headers,
            method='POST'
        )
        
        start_time = time.time()
        stop_event, _ = _start_live_timer("Transcribing")
        
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode())
            transcript = result.get('text', '')
            
            elapsed_time = time.time() - start_time
            stop_event.set()
            print(f"✅ Transcription completed in {elapsed_time:.1f}s")
            print(f"📊 Transcript length: {len(transcript)} characters")
            
            return transcript
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 401:
            print("❌ Error: Invalid OpenAI API key (401 Unauthorized)")
        elif e.code == 429:
            print("❌ Error: Rate limit exceeded or quota reached (429)")
        else:
            print(f"❌ OpenAI API error ({e.code}): {error_body}")
        sys.exit(1)
    except socket.timeout:
        print("❌ Network timeout while uploading/transcribing (increase timeout or check connectivity)")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during transcription: {e}")
        sys.exit(1)


def generate_summary_with_prompts(transcript, api_key, system_prompt, user_prompt_template):
    """Generate a structured Markdown summary from a transcript.

    Args:
        transcript: The transcription text to summarize.
        api_key: OpenAI API key used for authentication.
        system_prompt: System instruction given to the model.
        user_prompt_template: Template string into which the transcript is formatted.

    Returns:
        Tuple[str, int]: The generated summary and the total token usage reported by the API.

    Raises:
        SystemExit: If the API returns an error, a network error occurs, or a timeout happens.
    """
    print("🤖 Generating structured summary...")
    
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
            CHAT_ENDPOINT,
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )
        
        start_time = time.time()
        stop_event, _ = _start_live_timer("Generating")
        
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode())
            summary = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            elapsed_time = time.time() - start_time
            stop_event.set()
            print(f"✅ Summary generated in {elapsed_time:.1f}s")
            print(f"📊 Tokens used: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")
            
            return summary, total_tokens
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 401:
            print("❌ Error: Invalid OpenAI API key (401 Unauthorized)")
        elif e.code == 429:
            print("❌ Error: Rate limit exceeded or quota reached (429)")
        else:
            print(f"❌ OpenAI API error ({e.code}): {error_body}")
        sys.exit(1)
    except socket.timeout:
        print("❌ Network timeout while generating the summary (increase timeout or check connectivity)")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during summary generation: {e}")
        sys.exit(1)


def generate_summary(transcript, api_key):
    """Convenience wrapper around generate_summary_with_prompts with defaults.

    Args:
        transcript: The transcription text to summarize.
        api_key: OpenAI API key used for authentication.

    Returns:
        Tuple[str, int]: The generated summary and total token usage.

    Raises:
        SystemExit: Propagated from the underlying call when errors occur.
    """
    return generate_summary_with_prompts(transcript, api_key, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE)



def save_summary(summary, output_path):
    """Write the generated summary to a file on disk.

    Args:
        summary: Markdown content to persist.
        output_path: Path to the output Markdown file.

    Returns:
        None

    Raises:
        SystemExit: If the file cannot be written due to permissions or I/O error.
    """
    print(f"💾 Saving summary to {output_path}...")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ Summary saved successfully!")
    except PermissionError:
        print(f"❌ Error: Permission denied writing to file: {output_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)


def load_custom_prompts(prompt_file='prompt.json'):
    """Load custom prompts and language from a JSON file if present.

    Args:
        prompt_file: Path to a JSON file containing 'system_prompt', 'user_prompt', 'language'.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: System prompt, user prompt,
        and language code; each can be None if missing or file absent.

    Raises:
        SystemExit: If the file cannot be read or contains invalid JSON.
    """
    if not os.path.exists(prompt_file):
        return None, None, None
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            system = prompts.get('system_prompt')
            user = prompts.get('user_prompt')
            language = prompts.get('language')
            print(f"✅ Custom prompts loaded from {prompt_file}")
            return system, user, language
    except PermissionError:
        print(f"❌ Error: Permission denied reading {prompt_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {prompt_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading custom prompts: {e}")
        sys.exit(1)


def main():
    """Entry point for the CLI pipeline: transcribe then summarize or envoyer dans Notion."""
    import argparse

    parser = argparse.ArgumentParser(description="Transcribe and summarize a daily meeting, output as Markdown or to Notion.")
    parser.add_argument("audio_file", help="Path to the audio file to transcribe")
    parser.add_argument("prompt_file", nargs="?", default="prompt.json", help="JSON file for custom prompts (optional)")
    parser.add_argument("--notion", dest="notion_json", metavar="NOTION_JSON", help="Path to Notion DB schema JSON file (output-notion.json)")
    parser.add_argument("--notion-category", dest="notion_category", metavar="CATEGORY", help="Value for the Notion 'Category' select field (e.g. Standup)")
    parser.add_argument("--notion-title", dest="notion_title", metavar="TITLE", help="Title for the Notion page (default: date)")
    args = parser.parse_args()

    audio_path = args.audio_file
    prompt_file = args.prompt_file
    notion_json_path = args.notion_json
    notion_category = args.notion_category
    notion_title = args.notion_title

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    now_local = datetime.now()
    output_filename = OUTPUT_FILENAME_PATTERN.format(
        day=now_local.strftime('%d'),
        month=now_local.strftime('%m'),
        year=now_local.strftime('%y')
    )

    custom_system, custom_user, custom_language = load_custom_prompts(prompt_file)
    language = custom_language if custom_language else DEFAULT_LANGUAGE

    print(f"🚀 Starting daily meeting transcription pipeline")
    print(f"📁 Input file: {audio_path}")
    if notion_json_path:
        print(f"📦 Notion mode enabled, schema: {notion_json_path}")
    else:
        print(f"📄 Output file: {output_filename}")
    print(f"🌍 Language: {language}")
    print()

    # La suite (DRY_RUN, Notion, etc) sera ajoutée dans les étapes suivantes.
    # Pour l'instant, on garde le pipeline existant si --notion n'est pas utilisé.

    if not notion_json_path:
        transcript = transcribe_audio(audio_path, api_key, language)
        print()
        system_prompt = custom_system if custom_system else SYSTEM_PROMPT
        user_prompt_template = custom_user if custom_user else USER_PROMPT_TEMPLATE
        summary, tokens = generate_summary_with_prompts(transcript, api_key, system_prompt, user_prompt_template)
        print()
        save_summary(summary, output_filename)
        print()
        print(f"🎉 Pipeline completed successfully!")
        print(f"📊 Total tokens consumed: {tokens}")
    else:
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            print("❌ Error: NOTION_TOKEN environment variable not set")
            print("Set it with: export NOTION_TOKEN='your-notion-token'")
            sys.exit(1)

        # Generate the summary
        transcript = transcribe_audio(audio_path, api_key, language)
        print()
        system_prompt = custom_system if custom_system else SYSTEM_PROMPT
        user_prompt_template = custom_user if custom_user else USER_PROMPT_TEMPLATE
        summary, tokens = generate_summary_with_prompts(transcript, api_key, system_prompt, user_prompt_template)
        print()

        # Load the Notion DB schema
        try:
            with open(notion_json_path, 'r', encoding='utf-8') as f:
                notion_schema = json.load(f)
        except Exception as e:
            print(f"❌ Error loading Notion schema: {e}")
            sys.exit(1)

        db_id = notion_schema.get('id') or notion_schema.get('database_id')
        if not db_id:
            print("❌ Error: Database ID not found in Notion schema JSON.")
            sys.exit(1)

        # Prepare properties
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.isoformat(timespec='seconds').replace('+00:00', 'Z')
        # Dynamic mapping
        page_title = notion_title if notion_title else f"Daily {now_utc.strftime('%d/%m/%Y %H:%M')}"
        category = notion_category if notion_category else "Standup"

        properties = {
            "Name": {
                "title": [ { "text": { "content": page_title } } ]
            },
            "Date": {
                "date": { "start": date_str }
            },
            "Category": {
                "select": { "name": category }
            },
            "Attendees": {
                "people": []
            }
        }

        # Parse markdown into Notion blocks (heading, bulleted_list, paragraph)
        def markdown_to_notion_blocks(md):
            blocks = []
            lines = md.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                # Checklists: must be detected before bullet lists
                if line.startswith('- [ ]') or line.startswith('[ ]'):
                    content = line.replace('- [ ]', '').replace('[ ]', '').strip()
                    blocks.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [ { "text": { "content": content } } ],
                            "checked": False
                        }
                    })
                    i += 1
                elif line.startswith('### '):
                    blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [ { "text": { "content": line[4:].strip() } } ]
                        }
                    })
                    i += 1
                elif line.startswith('- '):
                    # bulleted list: collect all consecutive - lines (not checklists)
                    while i < len(lines) and lines[i].strip().startswith('- ') and not (lines[i].strip().startswith('- [ ]')):
                        item = lines[i].strip()[2:].strip()
                        blocks.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [ { "text": { "content": item } } ]
                            }
                        })
                        i += 1
                else:
                    # paragraph
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [ { "text": { "content": line } } ]
                        }
                    })
                    i += 1
            return blocks

        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [ { "text": { "content": "Daily summary" } } ]
                }
            }
        ]
        children += markdown_to_notion_blocks(summary)

        payload = {
            "parent": { "database_id": db_id.replace('-', '') },
            "properties": properties,
            "children": children
        }

        headers = {
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {notion_token}"
        }

        import urllib.request
        req = urllib.request.Request(
            url="https://api.notion.com/v1/pages",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()  # Ignore response content
                print(f"✅ Summary sent to Notion!")
        except urllib.error.HTTPError as e:
            print(f"❌ Notion API error ({e.code}): {e.read().decode()}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error during Notion API call: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

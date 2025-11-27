import os
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path
from loguru import logger

OPENAI_WHISPER_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"


def create_multipart_form_data(fields, files):
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


def transcribe_audio(audio_path: str, api_key: str, language: str = "fr") -> str:
    """Transcribes an audio file using the OpenAI Whisper API."""
    logger.info(f"\U0001F3A4 Starting audio transcription (language: {language})...")
    try:
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
    except FileNotFoundError:
        logger.error(f"\u274c Error: Audio file not found: {audio_path}")
        sys.exit(1)
    except PermissionError:
        logger.error(f"\u274c Error: Permission denied reading file: {audio_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\u274c Error reading audio file: {e}")
        sys.exit(1)
    try:
        file_size = os.path.getsize(audio_path)
        size_mb = file_size / (1024 * 1024)
        logger.info(f"\U0001F4E6 Audio size: {size_mb:.1f} MB")
        if size_mb > 24:
            logger.warning("Audio file is larger than 24MB. Whisper API may reject it.")
    except Exception as e:
        logger.warning(f"Could not determine audio file size: {e}")
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
    import time, socket
    try:
        request = urllib.request.Request(
            OPENAI_WHISPER_ENDPOINT,
            data=body,
            headers=headers,
            method='POST'
        )
        start_time = time.time()
        logger.info("⏱️Transcribing...")
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode())
            transcript = result.get('text', '')
            elapsed_time = time.time() - start_time
            logger.success(f"✅ Transcription completed in {elapsed_time:.1f}s")
            logger.info(f"📊 Transcript length: {len(transcript)} characters")
            return transcript
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 401:
            logger.error("❌ Error: Invalid OpenAI API key (401 Unauthorized)")
        elif e.code == 429:
            logger.error("❌ Error: Rate limit exceeded or quota reached (429)")
        else:
            logger.error(f"❌ OpenAI API error ({e.code}): {error_body}")
        sys.exit(1)
    except socket.timeout:
        logger.error("❌ Network timeout while uploading/transcribing (increase timeout or check connectivity)")
        sys.exit(1)
    except urllib.error.URLError as e:
        logger.error(f"❌ Network error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during transcription: {e}")
        sys.exit(1)

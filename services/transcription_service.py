import os
import tempfile
import urllib.request
import urllib.error
import json
from pathlib import Path
from loguru import logger
from pydub import AudioSegment
from utils.config import AppConfig


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


def transcribe_audio_chunk(audio_path: str, api_key: str, language: str) -> str:
    """Transcribes a single audio chunk."""
    try:
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
    except FileNotFoundError:
        logger.error(f"❌ Error: Audio file not found: {audio_path}")
        return ""
    except PermissionError:
        logger.error(f"❌ Error: Permission denied reading file: {audio_path}")
        return ""
    except Exception as e:
        logger.error(f"❌ Error reading audio file: {e}")
        return ""

    filename = os.path.basename(audio_path)
    ext = Path(audio_path).suffix.lower()
    content_type = f'audio/{ext.strip(".")}'

    boundary, body = create_multipart_form_data(
        fields={'model': AppConfig.whisper_model, 'language': language},
        files={'file': (filename, audio_content, content_type)}
    )
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }

    try:
        request = urllib.request.Request(
            AppConfig.openai_whisper_endpoint,
            data=body,
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode())
            return result.get('text', '')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        logger.error(f"❌ OpenAI API error ({e.code}): {error_body}")
        return ""
    except Exception as e:
        logger.error(f"❌ Unexpected error during transcription: {e}")
        return ""


def transcribe_audio(audio_path: str, api_key: str, language: str = "en") -> str:
    """Transcribes an audio file using the OpenAI Whisper API, splitting it into chunks if necessary."""
    logger.info(f"🎤 Starting audio transcription (language: {language})...")

    file_size = os.path.getsize(audio_path)
    size_mb = file_size / (1024 * 1024)
    logger.info(f"📦 Audio size: {size_mb:.1f} MB")

    max_size = 24 * 1024 * 1024
    if file_size < max_size:
        logger.info("Audio file is smaller than 24MB, transcribing directly.")
        return transcribe_audio_chunk(audio_path, api_key, language)

    logger.warning("Audio file is larger than 24MB. Splitting into chunks...")
    
    audio = AudioSegment.from_file(audio_path)
    
    # Calculate chunk size to be around 24MB
    duration_ms = len(audio)
    chunk_size_ms = int((max_size / file_size) * duration_ms)
    
    chunks = [audio[i:i + chunk_size_ms] for i in range(0, duration_ms, chunk_size_ms)]
    
    full_transcript = ""

    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(tmp_dir, f"chunk_{i}.mp3")
            logger.info(f"Transcribing chunk {i + 1}/{len(chunks)}...")
            chunk.export(chunk_path, format="mp3")

            transcript_chunk = transcribe_audio_chunk(chunk_path, api_key, language)
            if transcript_chunk:
                full_transcript += transcript_chunk + " "

    logger.success("✅ Transcription completed.")
    return full_transcript.strip()

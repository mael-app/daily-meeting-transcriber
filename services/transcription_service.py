import os
import subprocess
import tempfile
import urllib.request
import urllib.error
import json
from pathlib import Path
from loguru import logger
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


def _get_audio_duration(audio_path: str) -> float:
    """Returns audio duration in seconds using ffprobe."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', audio_path],
        capture_output=True,
        text=True
    )
    return float(json.loads(result.stdout)['format']['duration'])


def _split_audio(audio_path: str, chunk_duration: float, tmp_dir: str) -> list:
    """Splits audio into chunks of chunk_duration seconds using ffmpeg."""
    total_duration = _get_audio_duration(audio_path)
    chunks = []
    start = 0.0
    i = 0
    while start < total_duration:
        chunk_path = os.path.join(tmp_dir, f"chunk_{i}.mp3")
        subprocess.run(
            ['ffmpeg', '-i', audio_path, '-ss', str(start), '-t', str(chunk_duration),
             '-acodec', 'mp3', '-y', chunk_path],
            capture_output=True
        )
        chunks.append(chunk_path)
        start += chunk_duration
        i += 1
    return chunks


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
    logger.info(f"📦 Audio size: {file_size / (1024 * 1024):.1f} MB")

    max_size = 24 * 1024 * 1024
    if file_size < max_size:
        logger.info("Audio file is smaller than 24MB, transcribing directly.")
        return transcribe_audio_chunk(audio_path, api_key, language)

    logger.warning("Audio file is larger than 24MB. Splitting into chunks...")

    total_duration = _get_audio_duration(audio_path)
    chunk_duration = (max_size / file_size) * total_duration
    full_transcript = ""

    with tempfile.TemporaryDirectory() as tmp_dir:
        chunks = _split_audio(audio_path, chunk_duration, tmp_dir)
        for i, chunk_path in enumerate(chunks):
            logger.info(f"Transcribing chunk {i + 1}/{len(chunks)}...")
            transcript_chunk = transcribe_audio_chunk(chunk_path, api_key, language)
            if transcript_chunk:
                full_transcript += transcript_chunk + " "

    logger.success("✅ Transcription completed.")
    return full_transcript.strip()

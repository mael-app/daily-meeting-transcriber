# --- FastAPI server version ---

from loguru import logger
import sys
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import RedirectResponse
from typing import Optional
from services.audio_service import process_audio_service

app = FastAPI(
    title="Daily Meeting Transcriber API",
    description="API to transcribe and summarize daily meeting audio files. Interactive documentation available at /docs.",
    version="1.0.0"
)

logger.remove()
logger.add(sys.stdout, colorize=True,
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

logger.info("🚀 Application started with Loguru !")


@app.get("/health", summary="Healthcheck", tags=["Health"])
async def healthcheck():
    """
    Check if the API is alive.
    Returns status 200 and a simple message.
    """
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


@app.post(
    "/process-audio",
    summary="Transcribe and summarize an audio file",
    tags=["Transcription"],
    response_description="Transcript and summary generated from the audio file."
)
async def process_audio(
        file: UploadFile = File(..., description="Audio file to transcribe (any format supported by Whisper)"),
        notion_schema: Optional[UploadFile] = File(None, description="Notion DB schema (JSON, optional)")
):
    return process_audio_service(file, notion_schema)

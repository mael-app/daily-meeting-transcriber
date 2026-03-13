from dotenv import load_dotenv
load_dotenv()

import sys
import logging
from contextlib import asynccontextmanager
from loguru import logger
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import RedirectResponse
from typing import Optional
from services.audio_service import process_audio_service


# Route standard logging (uvicorn, etc.) through loguru
class _InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Daily Meeting Transcriber started")
    yield


app = FastAPI(
    title="Daily Meeting Transcriber API",
    description="API to transcribe and summarize daily meeting audio files. Interactive documentation available at /docs.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", summary="Healthcheck", tags=["Health"])
async def healthcheck():
    """Check if the API is alive. Returns status 200 and a simple message."""
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

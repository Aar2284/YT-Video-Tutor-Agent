from __future__ import annotations

import logging
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.transcript import fetch_transcript, Transcript
from src.chunking import chunk_transcript, Chunk
from src.qa_engine import QAEngine, QAResponse
from src.memory import ConversationMemory
from src.voice import speech_to_text, text_to_speech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory session store
sessions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sessions.clear()


app = FastAPI(
    title="Video Tutor Agent API",
    description="YouTube video Q&A with grounded answers and voice support",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class LoadVideoRequest(BaseModel):
    url: str
    languages: list[str] | None = None


class LoadVideoResponse(BaseModel):
    session_id: str
    video_id: str
    language: str
    segment_count: int
    message: str


class AskRequest(BaseModel):
    session_id: str
    question: str
    use_voice: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    is_refusal: bool
    audio_base64: str | None = None


class STTRequest(BaseModel):
    audio_base64: str
    language: str = "en"


class STTResponse(BaseModel):
    text: str


# --- Serve Frontend Static Files ---
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# --- API Endpoints ---

@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Video Tutor Agent API", "docs": "/docs"}


@app.post("/api/load-video", response_model=LoadVideoResponse)
async def load_video(req: LoadVideoRequest):
    try:
        transcript = fetch_transcript(req.url, req.languages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch transcript: {str(e)}")

    chunks = chunk_transcript(transcript)
    qa_engine = QAEngine(transcript, chunks)
    memory = ConversationMemory()

    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {
        "transcript": transcript,
        "chunks": chunks,
        "qa_engine": qa_engine,
        "memory": memory,
    }

    return LoadVideoResponse(
        session_id=session_id,
        video_id=transcript.video_id,
        language=transcript.language,
        segment_count=len(transcript.segments),
        message=f"Loaded video with {len(transcript.segments)} segments ({transcript.language})",
    )


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Load a video first.")

    qa_engine: QAEngine = session["qa_engine"]
    memory: ConversationMemory = session["memory"]

    memory.add_user_message(req.question)
    response: QAResponse = qa_engine.answer(
        req.question,
        conversation_history=memory.get_history(),
    )
    memory.add_assistant_message(response.answer)

    audio_b64 = None
    if req.use_voice:
        try:
            import base64
            audio_bytes = text_to_speech(response.answer)
            audio_b64 = base64.b64encode(audio_bytes).decode()
        except Exception as e:
            logger.warning(f"TTS failed: {e}")

    return AskResponse(
        answer=response.answer,
        sources=response.sources,
        is_refusal=response.is_refusal,
        audio_base64=audio_b64,
    )


@app.post("/api/stt", response_model=STTResponse)
async def speech_to_text_endpoint(req: STTRequest):
    try:
        import base64
        audio_bytes = base64.b64decode(req.audio_base64)
        text = speech_to_text(audio_bytes, req.language)
        return STTResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")


@app.post("/api/tts")
async def text_to_speech_endpoint(req: AskRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Use the last assistant answer or generate new one
    memory: ConversationMemory = session["memory"]
    if memory.is_empty:
        raise HTTPException(status_code=400, detail="No answer to convert to speech.")

    last_answer = memory.get_history()[-1]["content"]

    try:
        import base64
        audio_bytes = text_to_speech(last_answer)
        return {"audio_base64": base64.b64encode(audio_bytes).decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"message": "Session cleared"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "sessions": len(sessions)}

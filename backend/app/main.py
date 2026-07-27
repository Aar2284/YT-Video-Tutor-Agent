from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from .database import init_db, get_db
from .auth import hash_password, verify_password, create_token, get_current_user_id
from .transcript import get_transcript
from .graph import chat
from .speech import speech_to_text, text_to_speech, SpeechError
import re
import httpx

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://3.110.159.149:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

transcripts: dict[str, str] = {}


@app.on_event("startup")
def startup():
    init_db()


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?", (req.username,)
        ).fetchone()
        if exists:
            raise HTTPException(409, "Username already taken")
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (req.username, hash_password(req.password)),
        )
        user_id = cur.lastrowid
    token = create_token(user_id, req.username)
    return {"token": token, "username": req.username}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (req.username,)
        ).fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_token(row["id"], req.username)
    return {"token": token, "username": req.username}


@app.get("/api/auth/me")
def me(request: Request):
    user_id = get_current_user_id(request)
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    return {"id": row["id"], "username": row["username"]}


# ── Videos ───────────────────────────────────────────────────────────────────

class AddVideoRequest(BaseModel):
    url: str


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?#]+)",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url.strip())
        if m:
            return m.group(1)
    return None


def get_video_title(video_id: str) -> str:
    try:
        from pytubefix import YouTube
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return yt.title or ""
    except Exception:
        return ""


@app.post("/api/videos")
def add_video(req: AddVideoRequest, request: Request):
    user_id = get_current_user_id(request)
    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(400, "Invalid YouTube URL or video ID")

    title = get_video_title(video_id)
    thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM videos WHERE user_id = ? AND video_id = ?",
            (user_id, video_id),
        ).fetchone()
        if exists:
            return {
                "id": exists["id"],
                "video_id": video_id,
                "title": title,
                "thumbnail": thumbnail,
            }
        cur = conn.execute(
            "INSERT INTO videos (user_id, video_id, title, thumbnail) VALUES (?, ?, ?, ?)",
            (user_id, video_id, title, thumbnail),
        )
        video_row_id = cur.lastrowid

    return {
        "id": video_row_id,
        "video_id": video_id,
        "title": title,
        "thumbnail": thumbnail,
    }


@app.get("/api/videos")
def list_videos(request: Request):
    user_id = get_current_user_id(request)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, video_id, title, thumbnail, created_at FROM videos WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "video_id": r["video_id"],
            "title": r["title"],
            "thumbnail": r["thumbnail"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@app.delete("/api/videos/{video_row_id}")
def delete_video(video_row_id: int, request: Request):
    user_id = get_current_user_id(request)
    with get_db() as conn:
        conn.execute(
            "DELETE FROM videos WHERE id = ? AND user_id = ?",
            (video_row_id, user_id),
        )
    return {"status": "ok"}


# ── Ingest & Chat ────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    video_id: str
    transcript: str | None = None


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    video_id: str


import os
SUPADATA_KEY = os.getenv("SUPADATA_KEY", "")


@app.get("/api/transcript")
def get_transcript_proxy(video_id: str, request: Request):
    get_current_user_id(request)
    resp = httpx.get(
        f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}&text=true",
        headers={"x-api-key": SUPADATA_KEY},
        timeout=30,
    )
    if resp.status_code != 200:
        raise HTTPException(502, detail=f"Transcript API error: {resp.text[:200]}")
    return {"transcript": resp.text}


@app.post("/api/ingest")
def ingest(req: IngestRequest, request: Request):
    get_current_user_id(request)
    if req.video_id not in transcripts:
        if req.transcript:
            transcripts[req.video_id] = req.transcript
        else:
            try:
                transcripts[req.video_id] = get_transcript(req.video_id)
            except Exception as e:
                raise HTTPException(500, detail=f"Failed to get transcript: {e}")
    return {"status": "ok", "video_id": req.video_id, "length": len(transcripts[req.video_id])}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest, request: Request):
    get_current_user_id(request)
    if req.video_id not in transcripts:
        try:
            transcripts[req.video_id] = get_transcript(req.video_id)
        except Exception:
            transcripts[req.video_id] = ""
    context = transcripts[req.video_id]
    answer = chat(req.message, req.thread_id, context)
    return {"answer": answer, "thread_id": req.thread_id}


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Speech (STT / TTS) ───────────────────────────────────────────────────────

@app.post("/api/stt")
async def stt(request: Request, file: UploadFile = File(...)):
    get_current_user_id(request)
    audio = await file.read()
    if not audio:
        raise HTTPException(400, "Empty audio file")
    text = await speech_to_text(audio, file.filename or "audio.wav")
    return {"text": text}


class TTSRequest(BaseModel):
    text: str
    language: str = "en-IN"
    speaker: str = "shubh"


@app.post("/api/tts")
async def tts(req: TTSRequest, request: Request):
    get_current_user_id(request)
    try:
        audio_bytes = await text_to_speech(req.text, req.language, req.speaker)
    except SpeechError as e:
        raise HTTPException(e.status_code, detail=e.detail)
    if not audio_bytes:
        raise HTTPException(500, "TTS failed")
    return Response(content=audio_bytes, media_type="audio/wav")

# 🎓 Backend — YT Video Tutor Agent

> **FastAPI** + **LangGraph** + **Groq** + **SQLite** — A YouTube video tutor that transcribes, remembers, and answers questions grounded in the video transcript.

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [📦 Dependencies](#-dependencies)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🧩 Module Breakdown](#-module-breakdown)
- [🌐 API Endpoints](#-api-endpoints)
- [🏗️ Architecture Flow](#%EF%B8%8F-architecture-flow)
- [🔒 Authentication](#-authentication)
- [🗄️ Database Schema](#%EF%B8%8F-database-schema)
- [🤖 LLM Pipeline](#-llm-pipeline)
- [📝 Transcript Extraction](#-transcript-extraction)
- [🎤 Speech (STT / TTS)](#-speech-stt--tts)
- [🧪 Running Tests](#-running-tests)
- [⚠️ Known Limitations](#%EF%B8%8F-known-limitations)

---

## 🚀 Quick Start

```bash
# 1. Navigate to backend/
cd backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp ../.env.example ../.env
# Edit ../.env with your API keys

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

> ✅ Server starts at `http://localhost:8000`
> 📄 Auto-generated docs at `http://localhost:8000/docs`

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py        # 📦 Package marker
│   ├── config.py          # ⚙️  Environment & constants
│   ├── auth.py            # 🔐 Password hashing + JWT
│   ├── database.py        # 🗄️  SQLite layer
│   ├── llm.py             # 🧠 Groq LLM factory
│   ├── graph.py           # 🤖 LangGraph chat pipeline
│   ├── transcript.py      # 📝 Transcript extraction
│   ├── speech.py          # 🎤 STT / TTS (Sarvam + Deepgram)
│   └── main.py            # 🌐 FastAPI app & endpoints
├── data/
│   └── app.db             # 💾 SQLite database (auto-created)
└── requirements.txt       # 📋 Python dependencies
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.115.0 | Web framework |
| `uvicorn[standard]` | ≥ 0.30.0 | ASGI server |
| `python-dotenv` | ≥ 1.0.0 | Load `.env` files |
| `python-multipart` | ≥ 0.0.18 | File upload support |
| `httpx` | ≥ 0.27.0 | Async HTTP client |
| `langchain` | ≥ 0.3.0 | LLM framework |
| `langchain-core` | ≥ 0.3.0 | Core LangChain types |
| `langchain-groq` | ≥ 0.2.0 | Groq LLM integration |
| `langgraph` | ≥ 0.2.0 | Stateful agent graphs |
| `youtube-transcript-api` | ≥ 1.0.0 | YouTube captions API |
| `pytubefix` | ≥ 10.0.0 | YouTube audio download |
| `groq` | ≥ 0.13.0 | Groq Whisper STT |
| `bcrypt` | ≥ 4.0.0 | Password hashing |
| `PyJWT` | ≥ 2.8.0 | JWT tokens |

```bash
# Install all at once
pip install -r requirements.txt
```

---

## ⚙️ Configuration

All config lives in **`config.py`** and reads from `../../.env` (project root).

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | 🔑 Groq API key for LLM + Whisper |
| `SARVAM_API_KEY` | — | 🔑 Sarvam AI key for Indic STT |
| `DEEPGRAM_API_KEY` | — | 🔑 Deepgram key for TTS |
| `SUPADATA_KEY` | — | 🔑 Supadata key for transcript proxy |
| `JWT_SECRET` | `dev-secret-change-in-production` | 🔐 JWT signing secret |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | 🧠 Groq model name |
| `JWT_ALGORITHM` | `HS256` | 🔒 JWT algorithm |
| `JWT_EXPIRY_HOURS` | `72` | ⏰ Token validity (3 days) |

```bash
# Create your .env file
cp ../.env.example ../.env

# Add your keys
echo "GROQ_API_KEY=gsk_..." >> ../.env
echo "SARVAM_API_KEY=..." >> ../.env
echo "DEEPGRAM_API_KEY=..." >> ../.env
```

---

## 🧩 Module Breakdown

### `config.py` — ⚙️ Environment Loader

Loads `.env` from the project root and exposes constants.

```python
# Loads from ../../.env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
```

---

### `auth.py` — 🔐 Authentication

| Function | Description |
|----------|-------------|
| `hash_password(password)` | 🔒 Bcrypt hash with random salt |
| `verify_password(password, hashed)` | ✅/❌ Verify against bcrypt hash |
| `create_token(user_id, username)` | 🎫 Create JWT (72h expiry) |
| `decode_token(token)` | 📖 Decode & validate JWT |
| `get_current_user_id(request)` | 👤 Extract user from `Authorization: Bearer` header |

```bash
# Internals
Password → bcrypt.hashpw() → "$2b$12$..." (stored in DB)
Password + Hash → bcrypt.checkpw() → True / False
User ID + Username → jwt.encode() → "eyJhbG..."
```

---

### `database.py` — 🗄️ SQLite Layer

| Function | Description |
|----------|-------------|
| `get_db()` | 🔗 Context manager → connection with WAL + foreign keys |
| `init_db()` | 🏗️ Create `users` & `videos` tables (idempotent) |

**Database location:** `backend/data/app.db` (auto-created)

```sql
-- Schema
users (id, username, password_hash, created_at)
videos (id, user_id, video_id, title, thumbnail, created_at)
         └── FOREIGN KEY → users(id) ON DELETE CASCADE
         └── UNIQUE(user_id, video_id)
```

---

### `llm.py` — 🧠 LLM Factory

Single function that returns a `ChatGroq` instance.

```python
get_llm() → ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
```

---

### `graph.py` — 🤖 LangGraph Chat Pipeline

| Component | Description |
|-----------|-------------|
| `TutorState` | 📋 TypedDict: `messages` + `context` |
| `chatbot()` | 🧠 Prepends system prompt + transcript, invokes LLM |
| `tutor_graph` | 🔗 Compiled `StateGraph` with `MemorySaver` checkpointer |
| `chat(message, thread_id, context)` | 💬 Public API → runs graph → returns answer string |

```bash
# Flow
User message → chat() → tutor_graph.invoke()
  → chatbot() node:
      1. System prompt (AI tutor persona)
      2. Video transcript as context
      3. Conversation history (per thread_id)
      4. LLM response
  → Returns last message content
```

**Key features:**
- 🔒 Thread isolation via `thread_id`
- 📜 Memory persists across calls (`MemorySaver`)
- 🎯 Transcript injected as system context

---

### `transcript.py` — 📝 Transcript Extraction

| Function | Description |
|----------|-------------|
| `get_transcript(video_id)` | 📝 Two-tier extraction with fallback |
| `_whisper_transcribe(video_id)` | 🎤 Audio download + Groq Whisper fallback |

```bash
# Extraction pipeline
Video ID
  ├── Try 1: youtube-transcript-api (fast, free)
  │     ├── Fetch default language captions
  │     └── Fallback: first available language
  │
  └── Try 2: Whisper fallback (paid, slow)
        ├── pytubefix → download audio
        └── Groq Whisper → transcribe
```

---

### `speech.py` — 🎤 STT / TTS

| Function | Service | Model | Description |
|----------|---------|-------|-------------|
| `speech_to_text()` | Sarvam AI | `saaras:v3` | 🎤 Audio → text (async) |
| `text_to_speech()` | Deepgram | `aura` | 🔊 Text → WAV bytes (async) |

```bash
# STT
Audio bytes → POST /speech-to-text → {"transcript": "..."}

# TTS
Text (max 2500 chars) → POST /v1/speak → WAV bytes
```

---

### `main.py` — 🌐 FastAPI Application

The entry point. Creates the FastAPI app, adds CORS, and defines all endpoints.

```python
app = FastAPI()
# CORS: http://localhost:3000 (Next.js frontend)
# Transcripts cached in-memory: dict[video_id, transcript_text]
```

---

## 🌐 API Endpoints

### 🔐 Authentication

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/api/auth/register` | `{username, password}` | `{token, username}` | 📝 Register new user |
| `POST` | `/api/auth/login` | `{username, password}` | `{token, username}` | 🔑 Login |
| `GET` | `/api/auth/me` | — | `{id, username}` | 👤 Get current user |

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "pass123"}'

# Get profile (requires token)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Validation:**
- Username: minimum 3 characters
- Password: minimum 6 characters
- Duplicate usernames → `409 Conflict`

---

### 🎬 Videos

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/api/videos` | `{url}` | `{id, video_id, title, thumbnail}` | ➕ Add video |
| `GET` | `/api/videos` | — | `[{id, video_id, title, ...}]` | 📋 List videos |
| `DELETE` | `/api/videos/{id}` | — | `{status: "ok"}` | 🗑️ Delete video |

```bash
# Add video (supports multiple URL formats)
curl -X POST http://localhost:8000/api/videos \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Also works with:
#   - https://youtu.be/dQw4w9WgXcQ
#   - https://youtube.com/embed/dQw4w9WgXcQ
#   - dQw4w9WgXcQ  (bare 11-char ID)

# List all videos
curl http://localhost:8000/api/videos \
  -H "Authorization: Bearer TOKEN"

# Delete video
curl -X DELETE http://localhost:8000/api/videos/1 \
  -H "Authorization: Bearer TOKEN"
```

**Features:**
- ✅ Auto-fetches video title via `pytubefix`
- 🔁 Idempotent — adding same video twice returns same ID
- 🖼️ Auto-generates thumbnail URL

---

### 💬 Ingest & Chat

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/api/ingest` | `{video_id}` | `{status, video_id, length}` | 📥 Pre-fetch transcript |
| `POST` | `/api/chat` | `{message, thread_id, video_id}` | `{answer, thread_id}` | 💬 Ask a question |

```bash
# Pre-fetch transcript (optional, chat auto-fetches if needed)
curl -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ"}'

# Chat with the video
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this video about?",
    "thread_id": "thread-1",
    "video_id": "dQw4w9WgXcQ"
  }'
```

**Key behaviors:**
- 🔄 Chat auto-ingests transcript if not cached
- 🔒 Same `thread_id` = conversation memory persists
- 🎯 Answers grounded in transcript (refuses out-of-scope)

---

### 🎤 Speech

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| `POST` | `/api/stt` | `file` (multipart) | `{text}` | 🎤 Speech-to-text |
| `POST` | `/api/tts` | `{text, language, speaker}` | `audio/wav` | 🔊 Text-to-speech |

```bash
# Speech-to-text
curl -X POST http://localhost:8000/api/stt \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@recording.wav"

# Text-to-speech
curl -X POST http://localhost:8000/api/tts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en-IN", "speaker": "shubh"}'

# Supported languages
# en-IN, hi-IN, ta-IN, te-IN, bn-IN, mr-IN, gu-IN, kn-IN, ml-IN, or-IN, pa-IN
```

**TTS parameters:**

| Param | Default | Options |
|-------|---------|---------|
| `language` | `en-IN` | `en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `bn-IN`, etc. |
| `speaker` | `shubh` | `shubh`, `meera` |

---

### 🏥 Health

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| `GET` | `/health` | `{status: "ok"}` | ❤️ Health check |

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 🏗️ Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│              http://localhost:3000                       │
└─────────────────────┬───────────────────────────────────┘
                      │ CORS
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend (:8000)                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Auth     │  │  Videos  │  │  Chat    │  │ Speech │ │
│  │ register │  │  CRUD    │  │  ingest  │  │  STT   │ │
│  │ login    │  │  list    │  │  ask     │  │  TTS   │ │
│  │ me       │  │  delete  │  │          │  │        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │             │      │
│  ┌────▼─────┐  ┌─────▼────┐  ┌─────▼─────┐  ┌───▼───┐ │
│  │  bcrypt  │  │  SQLite  │  │ LangGraph │  │Sarvam │ │
│  │  JWT     │  │  (WAL)   │  │  + Groq   │  │Deepgram│ │
│  └──────────┘  └──────────┘  └─────┬─────┘  └───────┘ │
│                                    │                    │
│                              ┌─────▼─────┐              │
│                              │  Groq LLM │              │
│                              │  llama-3.3 │              │
│                              └───────────┘              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 External APIs                            │
│                                                         │
│  🧠 Groq         → LLM inference + Whisper STT         │
│  🎤 Sarvam AI    → Indic STT                           │
│  🔊 Deepgram     → TTS                                 │
│  📝 YouTube API  → Video captions                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Authentication

```
Request
  │
  ├─ No header → ❌ 401 "Not authenticated"
  │
  ├─ Header: "Token xyz" → ❌ 401 "Not authenticated"
  │
  ├─ Header: "Bearer <expired>" → ❌ 401 "Token expired"
  │
  ├─ Header: "Bearer <invalid>" → ❌ 401 "Invalid token"
  │
  └─ Header: "Bearer <valid_jwt>"
       │
       └─ Decode JWT → Extract user_id → Continue ✅
```

**JWT payload:**
```json
{
  "user_id": 42,
  "username": "alice",
  "exp": 1723478400
}
```

---

## 🗄️ Database Schema

```sql
┌─────────────────────────────────────────┐
│                users                     │
├─────────────────────────────────────────┤
│ id          INTEGER PRIMARY KEY AUTOINC │
│ username    TEXT UNIQUE NOT NULL        │
│ password_hash TEXT NOT NULL             │
│ created_at  TIMESTAMP DEFAULT NOW()    │
└──────────────────┬──────────────────────┘
                   │ 1:N
                   │ ON DELETE CASCADE
┌──────────────────▼──────────────────────┐
│                videos                    │
├─────────────────────────────────────────┤
│ id          INTEGER PRIMARY KEY AUTOINC │
│ user_id     INTEGER NOT NULL ──┐        │
│ video_id    TEXT NOT NULL      │        │
│ title       TEXT DEFAULT ''    │        │
│ thumbnail   TEXT DEFAULT ''    │        │
│ created_at  TIMESTAMP DEFAULT NOW()    │
├─────────────────────────────────────────┤
│ FOREIGN KEY (user_id) → users(id)      │
│ UNIQUE(user_id, video_id)              │
└─────────────────────────────────────────┘
```

---

## 🤖 LLM Pipeline

```
User: "What does the video explain about neural networks?"

         ┌──────────────────────────────────────┐
         │           System Message              │
         │  "You are an AI tutor. Use the       │
         │   transcript to answer questions..."  │
         └──────────────────────────────────────┘
                        │
         ┌──────────────────────────────────────┐
         │      Context Message (if any)         │
         │  "Video transcript:\n{full_text}"    │
         └──────────────────────────────────────┘
                        │
         ┌──────────────────────────────────────┐
         │       User Message (current)          │
         │  "What does the video explain         │
         │   about neural networks?"             │
         └──────────────────────────────────────┘
                        │
                   ┌────▼────┐
                   │  Groq   │
                   │  LLM    │
                   └────┬────┘
                        │
         ┌──────────────────────────────────────┐
         │        Assistant Response             │
         │  "The video explains that neural     │
         │   networks are..."                   │
         └──────────────────────────────────────┘
```

---

## 📝 Transcript Extraction

```bash
# Two-tier approach with automatic fallback

Tier 1: youtube-transcript-api (FREE, fast)
  │
  ├── 1. Try: ytt_api.fetch(video_id)
  │     └── ✅ Return " ".join(snippets)
  │
  └── 2. Fallback: list available languages
        ├── Found? → fetch with first language
        └── None?  → Fall through to Tier 2

Tier 2: Groq Whisper (PAID, slow)
  │
  ├── pytubefix → download audio stream
  ├── Save to temp file (.mp4)
  ├── Groq Whisper → transcribe audio
  └── Clean up temp file
```

**Transcript caching:** In-memory `dict` in `main.py`
- ⚡ Fast on repeat requests
- 💥 Lost on server restart (not persisted)

---

## 🎤 Speech (STT / TTS)

```
┌─────────── STT Flow ───────────┐
│                                │
│  Mic → WAV → POST /api/stt    │
│         │                      │
│         ▼                      │
│  Sarvam Saaras v3              │
│  (Indic language support)      │
│         │                      │
│         ▼                      │
│  {"transcript": "text"}       │
└────────────────────────────────┘

┌─────────── TTS Flow ───────────┐
│                                │
│  Text → POST /api/tts         │
│         │                      │
│         ▼                      │
│  Deepgram Aura                 │
│  (Multiple languages)          │
│         │                      │
│         ▼                      │
│  WAV audio bytes               │
└────────────────────────────────┘
```

---

## 🧪 Running Tests

```bash
# Run all tests (from project root)
py -3 -m pytest tests/ -v

# Run specific module tests
py -3 -m pytest tests/test_auth.py -v        # Auth only
py -3 -m pytest tests/test_database.py -v    # Database only
py -3 -m pytest tests/test_main.py -v        # API endpoints
py -3 -m pytest tests/test_transcript.py -v  # Transcript
py -3 -m pytest tests/test_graph.py -v       # LLM graph
py -3 -m pytest tests/test_config.py -v      # Config

# Run with short traceback
py -3 -m pytest tests/ -v --tb=short

# Run matching test names
py -3 -m pytest tests/ -k "register" -v
```

---

## ⚠️ Known Limitations

| # | Issue | Impact | Workaround |
|---|-------|--------|------------|
| 1 | 🔄 In-memory transcript cache | 💥 Lost on restart | Re-ingest on chat |
| 2 | 🔒 CORS locked to `localhost:3000` | 🚫 Can't access from other origins | Edit `allow_origins` in `main.py` |
| 3 | 🗄️ SQLite (not PostgreSQL) | ⚠️ No concurrent writes | Fine for single-user dev |
| 4 | 🤖 Single LLM node (no tool use) | 🎯 No web search / code exec | Add tools to LangGraph |
| 5 | 🎤 Deepgram TTS text limit | ✂️ Max 2500 chars per request | Split long text |

---

## 📂 File Reference

| File | Lines | Description |
|------|:-----:|-------------|
| `config.py` | 11 | ⚙️ Environment loading |
| `auth.py` | 43 | 🔐 Password hashing + JWT |
| `database.py` | 46 | 🗄️ SQLite operations |
| `llm.py` | 5 | 🧠 Groq LLM factory |
| `graph.py` | 40 | 🤖 LangGraph pipeline |
| `transcript.py` | 47 | 📝 Transcript extraction |
| `speech.py` | 46 | 🎤 STT / TTS |
| `main.py` | 269 | 🌐 FastAPI app + endpoints |
| **Total** | **507** | |

---

<div align="center">

**Built with ❤️ using FastAPI + LangGraph + Groq**

</div>

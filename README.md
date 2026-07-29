# 🎓 AI Tutor — YouTube Video Tutor Agent

> Chat with any YouTube video. Ask questions, get answers **grounded in the transcript**, speak naturally with voice I/O, and get help in **11 Indian languages**.

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-1C4E8A?style=flat&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-FF6B00?style=flat&logoColor=white" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white" />
</p>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🛠️ Tech Stack](#%EF%B8%8F-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [🏗️ Architecture](#%EF%B8%8F-architecture)
- [🌐 API Endpoints](#-api-endpoints)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🎨 Frontend Pages](#-frontend-pages)
- [🧪 Testing](#-testing)
- [🔒 Authentication](#-authentication)
- [⚠️ Known Limitations](#%EF%B8%8F-known-limitations)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📝 **Transcript Extraction** | Captions-first via `youtube-transcript-api`, fallback to audio download + Groq Whisper |
| 🤖 **Grounded Q&A** | LangGraph pipeline — answers only from the transcript, refuses out-of-scope questions |
| 🧠 **Multi-turn Memory** | Thread-based conversation memory persists across messages |
| 🎤 **Voice Input** | Browser mic → Sarvam AI Saaras v3 (STT) — auto-detects Indian languages |
| 🔊 **Voice Output** | Deepgram Aura (TTS) — hear the answer spoken aloud (English) |
| 🌍 **Indic STT** | Sarvam Saaras v3 auto-detects Indian languages (Hindi, Tamil, Telugu, etc.) |
| 🔐 **JWT Authentication** | Secure multi-user with bcrypt passwords + 72h token expiry |
| 🎬 **Video Management** | Add/list/delete videos — auto-fetches title & thumbnail |
| 🌑 **Dark Mode UI** | Beautiful dark theme with shadcn/ui components |
| ⚡ **Transcript Caching** | In-memory cache — no re-fetch on repeat questions |

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🌐 API | **FastAPI** + Uvicorn | REST API framework |
| 🤖 AI | **LangChain** + **LangGraph** | Stateful conversation pipeline |
| 🧠 LLM | **Groq** (llama-3.3-70b-versatile) | Fast LLM inference |
| 📝 Transcript | **youtube-transcript-api** | Free caption extraction |
| 🎤 Fallback STT | **Groq Whisper** (whisper-large-v3) | Audio transcription |
| 🗣️ Voice | **Sarvam AI** + **Deepgram** | Indic STT (Saaras v3) + English TTS (Aura) |
| 🗄️ Database | **SQLite** (WAL mode) | User & video storage |
| 🔐 Auth | **PyJWT** + **bcrypt** | JWT tokens + password hashing |
| 📡 HTTP | **httpx** (async) | API calls |

### Frontend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| ⚛️ Framework | **Next.js 16** + **React 19** | App Router, Server Components |
| 🎨 UI | **Tailwind CSS v4** + **shadcn/ui** | Dark theme, base-nova style |
| 💬 Chat | **assistant-ui** | Thread-based chat interface |
| 📦 State | **Zustand** | Auth state management |
| 📝 Language | **TypeScript** | Type-safe code |
| 🎤 Voice | **MediaRecorder API** | Browser mic recording |

---

## 🚀 Quick Start

### 1️⃣ Prerequisites

```bash
# Ensure you have
python --version    # Python 3.11+
node --version      # Node.js 18+
npm --version       # npm 9+
```

### 2️⃣ Clone & Setup

```bash
# Clone the repo
git clone <repo-url>
cd aaryan-codebase
```

### 3️⃣ Backend

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit ../.env with your API keys (see Configuration below)

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

> ✅ Backend running at `http://localhost:8000`
> 📄 API docs at `http://localhost:8000/docs`

### 4️⃣ Frontend

```bash
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

> ✅ Frontend running at `http://localhost:3000`

### 5️⃣ Open & Use

```
🌐 Open http://localhost:3000 in your browser
📝 Register an account
🎬 Add a YouTube video URL
💬 Start asking questions!
```

---

## 📁 Project Structure

```
aaryan-codebase/
│
├── 📄 README.md                    # This file
├── 📄 .env.example                 # API key template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 LICENSE                      # MIT License
├── 📄 transcript.py                # Standalone CLI transcript fetcher
│
├── 📂 backend/                     # 🐍 Python FastAPI backend
│   ├── 📄 README.md                # Backend documentation
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📂 data/                    # SQLite database (auto-created)
│   └── 📂 app/
│       ├── 📄 config.py            # ⚙️  Environment & constants
│       ├── 📄 auth.py              # 🔐 Password hashing + JWT
│       ├── 📄 database.py          # 🗄️  SQLite schema & operations
│       ├── 📄 llm.py               # 🧠 Groq LLM factory
│       ├── 📄 graph.py             # 🤖 LangGraph chat pipeline
│       ├── 📄 transcript.py        # 📝 Transcript extraction
│       ├── 📄 speech.py            # 🎤 STT / TTS (Sarvam + Deepgram)
│       └── 📄 main.py              # 🌐 FastAPI app & endpoints
│
├── 📂 frontend/                    # ⚛️  Next.js React frontend
│   ├── 📄 package.json             # Node dependencies
│   ├── 📄 next.config.ts           # Next.js config
│   ├── 📄 tsconfig.json            # TypeScript config
│   └── 📂 src/
│       ├── 📂 app/
│       │   ├── 📄 layout.tsx       # Root layout (dark theme)
│       │   ├── 📄 page.tsx         # Auth redirector
│       │   ├── 📄 globals.css      # Tailwind + shadcn theme
│       │   ├── 📂 login/           # 🔑 Login page
│       │   ├── 📂 register/        # 📝 Register page
│       │   ├── 📂 dashboard/       # 🎬 Video grid + management
│       │   └── 📂 chat/            # 💬 Chat UI with voice I/O
│       ├── 📂 components/
│       │   ├── 📂 assistant-ui/    # 🤖 8 chat components
│       │   └── 📂 ui/              # 🎨 11 shadcn components
│       └── 📂 lib/
│           ├── 📄 api.ts           # 📡 Fetch wrapper + auth
│           ├── 📄 auth.ts          # 🔐 Zustand auth store
│           └── 📄 utils.ts         # 🔧 cn() helper
│
└── 📂 tests/                       # 🧪 Test suite
    ├── 📄 README.md                # Test documentation
    ├── 📄 conftest.py              # 🔧 Shared fixtures
    ├── 📄 test_config.py           # ⚙️  Config tests
    ├── 📄 test_auth.py             # 🔐 Auth tests
    ├── 📄 test_database.py         # 🗄️  Database tests
    ├── 📄 test_transcript.py       # 📝 Transcript tests
    ├── 📄 test_graph.py            # 🤖 LLM graph tests
    └── 📄 test_main.py             # 🌐 API endpoint tests
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       👤 User (Browser)                         │
│                        localhost:3000                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │   Next.js 16  │
                    │   React 19    │
                    │   Tailwind    │
                    └───────┬───────┘
                            │  HTTP / WebSocket
                            │  CORS
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend (:8000)                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  🔐 Auth    │  │  🎬 Videos  │  │  💬 Chat    │            │
│  │  register   │  │  add/list   │  │  ingest     │            │
│  │  login      │  │  delete     │  │  ask        │            │
│  │  me         │  │             │  │             │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐            │
│  │  bcrypt     │  │  SQLite     │  │  LangGraph  │            │
│  │  JWT        │  │  (WAL)      │  │  + Groq LLM │            │
│  └─────────────┘  └─────────────┘  └──────┬──────┘            │
│                                            │                    │
│  ┌─────────────┐                    ┌──────▼──────┐            │
│  │  🎤 Speech  │                    │  Transcript  │            │
│  │  Sarvam +   │                    │  Extraction  │            │
│  │  Deepgram   │                    │              │            │
│  └─────────────┘                    └──────┬──────┘            │
│                                            │                    │
└────────────────────────────────────────────┼────────────────────┘
                                             │
                    ┌────────────────────────┼───────────────────┐
                    │              External APIs                 │
                    │                                            │
                    │  🧠 Groq        → LLM + Whisper STT       │
                    │  🎤 Sarvam AI   → Indic STT               │
                    │  🔊 Deepgram    → TTS                     │
                    │  📝 YouTube     → Video captions          │
                    └────────────────────────────────────────────┘
```

---

## 🌐 API Endpoints

### 🔐 Authentication

| Method | Endpoint | Auth | Body | Response |
|--------|----------|:----:|------|----------|
| `POST` | `/api/auth/register` | ❌ | `{username, password}` | `{token, username}` |
| `POST` | `/api/auth/login` | ❌ | `{username, password}` | `{token, username}` |
| `GET` | `/api/auth/me` | ✅ | — | `{id, username}` |

### 🎬 Videos

| Method | Endpoint | Auth | Body | Response |
|--------|----------|:----:|------|----------|
| `POST` | `/api/videos` | ✅ | `{url}` | `{id, video_id, title, thumbnail}` |
| `GET` | `/api/videos` | ✅ | — | `[{id, video_id, title, ...}]` |
| `DELETE` | `/api/videos/{id}` | ✅ | — | `{status: "ok"}` |

### 💬 Chat

| Method | Endpoint | Auth | Body | Response |
|--------|----------|:----:|------|----------|
| `POST` | `/api/ingest` | ✅ | `{video_id}` | `{status, video_id, length}` |
| `POST` | `/api/chat` | ✅ | `{message, thread_id, video_id}` | `{answer, thread_id}` |

### 🎤 Speech

| Method | Endpoint | Auth | Body | Response |
|--------|----------|:----:|------|----------|
| `POST` | `/api/stt` | ✅ | `file` (multipart) | `{text}` |
| `POST` | `/api/tts` | ✅ | `{text, language, speaker}` | `audio/wav` |

### 🏥 Health

| Method | Endpoint | Auth | Response |
|--------|----------|:----:|----------|
| `GET` | `/health` | ❌ | `{status: "ok"}` |

```bash
# Quick test — health check
curl http://localhost:8000/health

# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'

# Chat with a video
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this video about?", "thread_id": "t1", "video_id": "dQw4w9WgXcQ"}'
```

---

## ⚙️ Configuration

### Environment Variables

Create `/.env` from `/.env.example`:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GROQ_API_KEY` | ✅ | — | 🔑 Groq API key (LLM + Whisper) |
| `SARVAM_API_KEY` | ✅ | — | 🔑 Sarvam AI key (Indic STT) |
| `DEEPGRAM_API_KEY` | ✅ | — | 🔑 Deepgram key (TTS) |
| `SUPADATA_KEY` | ❌ | — | 🔑 Supadata key (transcript proxy) |
| `JWT_SECRET` | ❌ | `dev-secret-change-in-production` | 🔐 JWT signing secret |
| `NEXT_PUBLIC_BACKEND_URL` | ❌ | `http://localhost:8000` | 🔗 Backend URL for frontend |

### Getting API Keys

| API | What It Does | Free Tier | Sign Up |
|-----|-------------|-----------|---------|
| 🧠 **Groq** | LLM inference + Whisper STT | ✅ Free | [console.groq.com](https://console.groq.com) |
| 🎤 **Sarvam AI** | Indic STT | ✅ Free credits | [sarvam.ai](https://sarvam.ai) |
| 🔊 **Deepgram** | Text-to-speech | ✅ Free credits | [console.deepgram.com](https://console.deepgram.com/signup) |

```bash
# Example .env file
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
SARVAM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
DEEPGRAM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
JWT_SECRET=my-super-secret-key-change-this
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## 🎨 Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| 🏠 **Root** | `/` | Redirects to `/dashboard` (logged in) or `/login` |
| 🔑 **Login** | `/login` | Username + password login form |
| 📝 **Register** | `/register` | Create new account (min 3 char username, 6 char password) |
| 🎬 **Dashboard** | `/dashboard` | Video grid — add, view, delete videos |
| 💬 **Chat** | `/chat?videoId=...` | Full chat UI with mic button + TTS playback |

### Chat UI Features

```
┌─────────────────────────────────────────────────┐
│  🎬 Video: "Neural Networks Explained"         │
├─────────────────────────────────────────────────┤
│                                                 │
│  👤 You: What are neural networks?              │
│                                                 │
│  🤖 AI: Neural networks are computing systems   │
│     inspired by biological neural networks...   │
│     (Grounded in transcript)                    │
│                                                 │
│  👤 You: How do they learn?                     │
│                                                 │
│  🤖 AI: They learn through a process called     │
│     backpropagation, where the network...       │
│                                                 │
├─────────────────────────────────────────────────┤
│  🎤 [Speak]    Type your question...    [Send]  │
│  🔊 [Play TTS]                             🔇   │
└─────────────────────────────────────────────────┘
```

---

## 🧪 Testing

```bash
# Run ALL tests
py -3 -m pytest tests/ -v

# Run specific test file
py -3 -m pytest tests/test_auth.py -v
py -3 -m pytest tests/test_main.py -v
py -3 -m pytest tests/test_database.py -v

# Run with short traceback
py -3 -m pytest tests/ -v --tb=short

# Run tests matching keyword
py -3 -m pytest tests/ -k "register" -v
```

### Test Coverage

| File | Tests | What It Covers |
|------|:-----:|----------------|
| `test_config.py` | 3 | ⚙️ Config loading, env fallbacks |
| `test_auth.py` | 6 | 🔐 bcrypt hashing, JWT lifecycle, auth middleware |
| `test_database.py` | 2 | 🗄️ Schema creation, context manager |
| `test_transcript.py` | 7 | 📝 URL parsing, video ID extraction |
| `test_graph.py` | 3 | 🤖 LLM state definition, system prompt |
| `test_main.py` | 10 | 🌐 All API endpoints — auth, videos, chat |

> 📖 See [tests/README.md](tests/README.md) for detailed test documentation

---

## 🔒 Authentication Flow

```
Register/Login
  │
  ├─ Password → bcrypt.hashpw() → Stored in DB
  │
  └─ Returns JWT token (72h expiry)
       │
       └─ Use in requests:
            Authorization: Bearer eyJhbG...
```

**Validation rules:**
- 👤 Username: minimum **3 characters**
- 🔒 Password: minimum **6 characters**
- 🎫 Token expires after **72 hours**
- 🔐 HMAC-SHA256 signing (HS256)

---

## 📊 How It Works

```
User adds YouTube URL
  │
  ▼
┌─────────────────────────────────┐
│  📝 Transcript Extraction       │
│                                 │
│  Try 1: youtube-transcript-api  │
│    ├─ ✅ Free, fast             │
│    └─ ❌ No captions? →         │
│                                 │
│  Try 2: Groq Whisper            │
│    ├─ Download audio (pytubefix)│
│    └─ Transcribe with Whisper   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  💬 Chat with AI Tutor          │
│                                 │
│  System prompt + Transcript     │
│  + Conversation history         │
│  + User question                │
│       │                         │
│       ▼                         │
│  Groq LLM (llama-3.3-70b)      │
│       │                         │
│       ▼                         │
│  Grounded answer                │
│  (or refusal if out-of-scope)   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  🎤 Optional Voice Output       │
│                                 │
│  Text → Deepgram Aura           │
│       → WAV audio               │
│       → Play in browser         │
└─────────────────────────────────┘
```

---

## ⚠️ Known Limitations

| # | Issue | Status |
|---|-------|--------|
| 1 | 🔄 Transcript cache is in-memory — lost on server restart | ⚠️ By design |
| 2 | 🗄️ SQLite — not ideal for high-concurrency production | ⚠️ Fine for dev |
| 3 | 🔒 CORS locked to `localhost:3000` | 🔧 Edit `main.py` to change |
| 4 | 🤖 No tool-use / web search in LLM pipeline | 📋 Future enhancement |

---

## 📂 Related Docs

| Document | Description |
|----------|-------------|
| [backend/README.md](backend/README.md) | 📖 Full backend API documentation |
| [frontend/README.md](frontend/README.md) | ⚛️ Full frontend documentation |
| [tests/README.md](tests/README.md) | 🧪 Test suite documentation |

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ using FastAPI + Next.js + LangGraph + Groq**

[⬆ Back to Top](#-ai-tutor--youtube-video-tutor-agent)

</div>

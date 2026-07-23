# Video Tutor Agent

A tutor agent that ingests a YouTube educational video, transcribes it, and answers user doubts (text + voice) strictly grounded in that transcript.

## Features

- **YouTube transcript extraction** — captions-first, with yt-dlp + Whisper fallback
- **Grounded Q&A** — answers only from the transcript, refuses out-of-scope questions
- **Timestamp citations** — answers cite approximate timestamps from the video
- **Multi-turn memory** — follow-up questions use conversation history
- **Voice I/O** — speak questions (STT) and hear answers (TTS)
- **Multilingual support** — Hindi/Tamil/etc. via Sarvam AI APIs

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd video-tutor-agent
pip install -r requirements.txt

# 2. (Optional) Add API keys for LLM + voice features
cp .env.example .env
# Edit .env with your keys

# 3. Run the app
streamlit run app.py
```

## How It Works

```
YouTube URL
  → Transcript extraction (captions API, fallback: yt-dlp + STT)
  → Chunking + retrieval for long videos
  → Grounded LLM Q&A (refuses out-of-scope questions)
  → TTS for spoken output (optional)
  → Streamlit UI (chat + mic input/output)
```

## API Keys

| API | What It Does | Free Tier |
|-----|-------------|-----------|
| **Sarvam AI** | Indic STT + TTS (Hindi, Tamil, etc.) | Free credits at sarvam.ai |
| **Groq** | Fast LLM for Q&A answers | Free at console.groq.com |

```bash
# Add your keys to .env
cp .env.example .env
# Edit .env with:
# SARVAM_API_KEY=your_sarvam_key
# GROQ_API_KEY=your_groq_key
```

## Project Structure

```
├── app.py                 # Streamlit entrypoint
├── src/
│   ├── transcript.py      # Caption extraction + yt-dlp fallback
│   ├── chunking.py        # Split + embed for long videos
│   ├── qa_engine.py       # Grounded LLM Q&A + refusal logic
│   ├── voice.py           # STT/TTS wrappers
│   ├── memory.py          # Multi-turn conversation state
│   └── utils.py           # Helpers
├── tests/
│   └── eval_grounding.py  # Hallucination checks
└── demo/                  # Demo assets
```

## Quality Checklist

- [x] Works end-to-end on fresh videos
- [x] Correctly refuses out-of-scope questions
- [ ] Handles non-English videos natively (needs Sarvam key)
- [ ] Voice loop works (needs API keys)
- [x] No crash on bad input
- [x] Clean git history with incremental commits

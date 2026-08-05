# 🧪 Test Suite — YT Video Tutor Agent

> **6 test files** | **29 tests** | **100% modules covered**

---

## 📋 Table of Contents

| # | File | Tests | Coverage |
|---|------|:-----:|----------|
| 1 | 📦 [test_config.py](#-test_configpy) | 3 | Environment & config loading |
| 2 | 🔐 [test_auth.py](#-test_authpy) | 6 | Password hashing & JWT tokens |
| 3 | 🗄️ [test_database.py](#-test_databasepy) | 2 | SQLite DB init & context manager |
| 4 | 📝 [test_transcript.py](#-test_transcriptpy) | 7 | YouTube URL parsing & video ID extraction |
| 5 | 🤖 [test_graph.py](#-test_graphpy) | 4 | LangGraph state & system prompt |
| 6 | 🌐 [test_main.py](#-test_mainpy) | 7 | FastAPI endpoints (integration) |

---

## 🚀 Quick Start

```bash
# Install dependencies (if not already)
pip install pytest

# Run ALL tests
py -3 -m pytest tests/ -v

# Run a specific test file
py -3 -m pytest tests/test_auth.py -v

# Run with short traceback
py -3 -m pytest tests/ -v --tb=short

# Run tests matching a keyword
py -3 -m pytest tests/ -k "register" -v
```

---

## 📦 `test_config.py`

> Tests that `backend/app/config.py` loads environment variables correctly.

| Test | Description |
|------|-------------|
| `test_groq_model_is_set` | ✅ `GROQ_MODEL` is loaded |
| `test_jwt_algorithm` | ✅ JWT algorithm is `HS256` |
| `test_jwt_expiry_hours` | ✅ Expiry is positive integer |

```bash
# Run config tests only
py -3 -m pytest tests/test_config.py -v
```

---

## 🔐 `test_auth.py`

> Tests password hashing (`bcrypt`) and JWT token lifecycle.

### Password Hashing

| Test | Description |
|------|-------------|
| `test_hash_password_returns_string` | Hash output is a string |
| `test_verify_password_correct` | ✅ Correct password verifies |
| `test_verify_password_incorrect` | ❌ Wrong password rejects |
| `test_different_hashes_for_same_password` | 🎲 Bcrypt uses random salt (different outputs) |

### JWT Tokens

| Test | Description |
|------|-------------|
| `test_create_and_decode_token` | Create → decode roundtrip works |
| `test_decode_invalid_token` | Garbage token raises exception |

```bash
# Run auth tests only
py -3 -m pytest tests/test_auth.py -v
```

---

## 🗄️ `test_database.py`

> Tests SQLite database initialization and context manager.

| Test | Description |
|------|-------------|
| `test_init_db_creates_tables` | `users` and `videos` tables exist |
| `test_get_db_context_manager` | Connection returns correct query result |

```bash
# Run database tests only
py -3 -m pytest tests/test_database.py -v
```

---

## 📝 `test_transcript.py`

> Tests YouTube URL parsing and video ID extraction.

### URL Parsing

| Test | Description |
|------|-------------|
| `test_standard_youtube_url` | `youtube.com/watch?v=ID` → ID |
| `test_short_youtube_url` | `youtu.be/ID` → ID |
| `test_embed_youtube_url` | `youtube.com/embed/ID` → ID |
| `test_plain_video_id` | Bare ID → ID |
| `test_invalid_url` | Google URL → `None` |
| `test_empty_string` | Empty → `None` |
| `test_url_with_extra_params` | URL with `&list=` → correct ID |

```bash
# Run transcript tests only
py -3 -m pytest tests/test_transcript.py -v
```

---

## 🤖 `test_graph.py`

> Tests the LangGraph chat pipeline state definition and system prompt.

| Test | Description |
|------|-------------|
| `test_tutor_state_has_required_keys` | `messages` + `context` in annotations |
| `test_system_prompt_is_string` | System prompt is a string |
| `test_system_prompt_mentions_tutor` | Mentions "tutor" |
| `test_system_prompt_mentions_transcript` | Mentions "transcript" |

```bash
# Run graph tests only
py -3 -m pytest tests/test_graph.py -v
```

---

## 🌐 `test_main.py`

> Full integration tests against all FastAPI API endpoints.

### Health

| Test | Description |
|------|-------------|
| `test_health_returns_ok` | `GET /health` → `{"status": "ok"}` |

### Auth Endpoints

| Test | Description |
|------|-------------|
| `test_register_missing_fields` | ❌ Empty body → 422 |
| `test_login_missing_fields` | ❌ Empty body → 422 |
| `test_register_username_too_short` | ❌ Username < 3 chars → 400 |
| `test_register_password_too_short` | ❌ Password < 6 chars → 400 |

### Video Endpoints

| Test | Description |
|------|-------------|
| `test_add_video_no_auth` | ❌ No token → 401 |
| `test_list_videos_no_auth` | ❌ No token → 401 |

```bash
# Run all endpoint tests
py -3 -m pytest tests/test_main.py -v

# Run only auth endpoint tests
py -3 -m pytest tests/test_main.py -k "Register or Login" -v

# Run only video tests
py -3 -m pytest tests/test_main.py -k "Video" -v
```

---

## 🏗️ Architecture

```
tests/
├── conftest.py              # 🔧 Shared fixtures
├── test_config.py           # 📦 Config loading
├── test_auth.py             # 🔐 Auth (bcrypt + JWT)
├── test_database.py         # 🗄️ SQLite operations
├── test_transcript.py       # 📝 URL parsing
├── test_graph.py            # 🤖 LangGraph state
└── test_main.py             # 🌐 API endpoint integration
```

### Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `anyio_backend` | session | Async backend config |

---

## 📊 Run Everything

```bash
# Full suite with verbose output
py -3 -m pytest tests/ -v

# Full suite with short traceback
py -3 -m pytest tests/ -v --tb=short
```

---

## ⚠️ Notes

- External APIs (**Groq**, **Sarvam AI**, **Deepgram**, **YouTube**) are **not** mocked — some tests may fail without valid API keys
- Each test gets a **fresh temp database** — tests are fully isolated
- The `tests/__init__.py` makes the `tests/` directory a Python package
- Uses FastAPI's `TestClient` — no actual server needed for API tests

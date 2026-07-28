# ⚛️ Frontend — AI Tutor

> **Next.js 16** + **React 19** + **Tailwind CSS v4** + **shadcn/ui** — A beautiful dark-mode chat interface for talking to YouTube videos.

---

## 📋 Table of Contents

- [🛠️ Tech Stack](#%EF%B8%8F-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [📄 Pages](#-pages)
- [🧩 Components](#-components)
- [📚 Lib Modules](#-lib-modules)
- [🎨 Styling & Theming](#-styling--theming)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🔗 Backend Integration](#-backend-integration)
- [🎤 Voice Features](#-voice-features)
- [📂 File Reference](#-file-reference)

---

## 🛠️ Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| 🖥️ Framework | **Next.js** (App Router) | 16.2.11 |
| ⚛️ UI Library | **React** | 19.2.4 |
| 📝 Language | **TypeScript** (strict mode) | 5.x |
| 🎨 Styling | **Tailwind CSS** | v4 |
| 🧱 UI Components | **shadcn/ui** (base-nova style) | v4 |
| 💬 Chat UI | **assistant-ui** | 0.14.27 |
| 🤖 AI SDK | **Vercel AI SDK** | v7 |
| 📦 State | **Zustand** | 5.x |
| 🎨 Icons | **Lucide React** | 1.26.0 |
| 📝 Markdown | **remark-gfm** | 4.x |

---

## 🚀 Quick Start

### Prerequisites

```bash
node --version    # Node.js 18+
npm --version     # npm 9+
```

### Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

> ✅ Running at `http://localhost:3000`

### Available Scripts

```bash
npm run dev       # 🚀 Start development server
npm run build     # 📦 Production build
npm run start     # ▶️  Start production server
npm run lint      # 🔍 Run ESLint
```

---

## 📁 Project Structure

```
frontend/
├── 📄 package.json              # Dependencies & scripts
├── 📄 next.config.ts            # Next.js config (empty)
├── 📄 tsconfig.json             # TypeScript config (strict)
├── 📄 eslint.config.mjs         # ESLint 9 flat config
├── 📄 postcss.config.mjs        # Tailwind PostCSS plugin
├── 📄 components.json           # shadcn/ui config
├── 📄 .env.local                # Local env vars (gitignored)
│
└── 📂 src/
    ├── 📂 app/
    │   ├── 📄 globals.css       # 🎨 Tailwind + shadcn theme
    │   ├── 📄 layout.tsx        # 🏗️  Root layout (dark, Geist)
    │   ├── 📄 page.tsx          # 🔀 Auth redirector
    │   ├── 📂 login/            # 🔑 Login page
    │   │   └── 📄 page.tsx
    │   ├── 📂 register/         # 📝 Register page
    │   │   └── 📄 page.tsx
    │   ├── 📂 dashboard/        # 🎬 Video management
    │   │   └── 📄 page.tsx
    │   └── 📂 chat/             # 💬 AI chat interface
    │       └── 📄 page.tsx
    │
    ├── 📂 components/
    │   ├── 📂 assistant-ui/     # 🤖 8 chat components
    │   │   ├── 📄 attachment.tsx
    │   │   ├── 📄 follow-up-suggestions.tsx
    │   │   ├── 📄 markdown-text.tsx
    │   │   ├── 📄 reasoning.tsx
    │   │   ├── 📄 thread.tsx
    │   │   ├── 📄 tool-fallback.tsx
    │   │   ├── 📄 tool-group.tsx
    │   │   └── 📄 tooltip-icon-button.tsx
    │   │
    │   └── 📂 ui/               # 🎨 11 shadcn primitives
    │       ├── 📄 avatar.tsx
    │       ├── 📄 badge.tsx
    │       ├── 📄 button.tsx
    │       ├── 📄 card.tsx
    │       ├── 📄 collapsible.tsx
    │       ├── 📄 dialog.tsx
    │       ├── 📄 input.tsx
    │       ├── 📄 scroll-area.tsx
    │       ├── 📄 separator.tsx
    │       ├── 📄 textarea.tsx
    │       └── 📄 tooltip.tsx
    │
    └── 📂 lib/
        ├── 📄 api.ts            # 📡 Fetch wrapper + auth
        ├── 📄 auth.ts           # 🔐 Zustand auth store
        └── 📄 utils.ts          # 🔧 cn() helper
```

---

## 📄 Pages

### 🔀 Root Page (`/`)

```
┌─────────────────────────────────────┐
│                                     │
│          ⏳ Loading...              │
│         (pulse animation)          │
│                                     │
└─────────────────────────────────────┘
         │
         ├─ Logged in?  → /dashboard
         └─ Not logged in? → /login
```

Auth check on mount → automatic redirect. No UI rendered.

---

### 🔑 Login (`/login`)

```
┌─────────────────────────────────────┐
│                                     │
│            🎓 AI Tutor              │
│        Sign in to your account      │
│                                     │
│    ┌─────────────────────────┐      │
│    │  Username               │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │  Password               │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │       Sign in           │      │
│    └─────────────────────────┘      │
│                                     │
│   Don't have an account? Sign up    │
│                                     │
└─────────────────────────────────────┘
```

| Feature | Detail |
|---------|--------|
| Fields | Username + Password |
| Validation | Required fields |
| Error display | Red banner on failure |
| Loading state | Button disabled + "Signing in..." |
| Link | → `/register` |

---

### 📝 Register (`/register`)

```
┌─────────────────────────────────────┐
│                                     │
│            🎓 AI Tutor              │
│          Create your account        │
│                                     │
│    ┌─────────────────────────┐      │
│    │  Username (min 3 chars) │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │  Password (min 6 chars) │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │  Confirm password       │      │
│    └─────────────────────────┘      │
│    ┌─────────────────────────┐      │
│    │    Create account       │      │
│    └─────────────────────────┘      │
│                                     │
│   Already have an account? Sign in  │
│                                     │
└─────────────────────────────────────┘
```

| Feature | Detail |
|---------|--------|
| Fields | Username + Password + Confirm |
| Validation | `minLength={3}` username, `minLength={6}` password |
| Client check | Password mismatch → "Passwords don't match" |
| Link | → `/login` |

---

### 🎬 Dashboard (`/dashboard`)

```
┌─────────────────────────────────────────────────────────┐
│  🎓 AI Tutor              👤 alice        [Sign out]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │ 🖼️ thumb  │  │ 🖼️ thumb  │  │ 🖼️ thumb  │          │
│  │ Title...  │  │ Title...  │  │ Title...  │          │
│  │ 2 days ago│  │ 1 week ago│  │ 3 hrs ago │          │
│  │ [🗑️]     │  │ [🗑️]     │  │ [🗑️]     │          │
│  └───────────┘  └───────────┘  └───────────┘          │
│                                                         │
│                        [+ Add Video]                    │
└─────────────────────────────────────────────────────────┘
```

| Feature | Detail |
|---------|--------|
| Auth guard | Redirects to `/login` if not authenticated |
| Video grid | Responsive 1/2/3 columns |
| Add video | Modal with URL input → auto-navigates to chat |
| Delete video | Click 🗑️ icon on card |
| Thumbnails | Auto-fetched from YouTube (`img.youtube.com`) |
| Empty state | "No videos yet" with CTA button |
| Loading | Skeleton placeholders |

---

### 💬 Chat (`/chat?videoId=...`)

```
┌─────────────────────────────────────────────────────────┐
│  ← 🎓 AI Tutor        video: dQw4w9WgXcQ               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ✨ Ask anything about this video                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│                          ┌──────────────────────┐      │
│                          │ 👤 What is this       │      │
│                          │    video about?       │      │
│                          └──────────────────────┘      │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │ 🤖 This video explains neural networks...    │      │
│  │    (grounded in transcript)           🔊 ▶️  │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
│                          ┌──────────────────────┐      │
│                          │ 👤 How do they learn? │      │
│                          └──────────────────────┘      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [🎤]  ┌──────────────────────────────┐  [➤]          │
│  Mic   │ Type your question...        │  Send          │
│        └──────────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

| Feature | Detail |
|---------|--------|
| Video ID | From `?videoId=` URL parameter |
| Pre-warm | Auto-calls `POST /api/ingest` on mount |
| Thread | Unique `thread_id` per session (`crypto.randomUUID()`) |
| Messages | User (right, dark) + Assistant (left, muted) |
| Auto-scroll | Scrolls to bottom on new messages |
| Loading | Bouncing dots animation |
| Error handling | Shows error banner on init/send failures |

**🎤 Voice Input (STT):**
- Click mic button → records audio (MediaRecorder API)
- Red pulse animation while recording
- Sends to `POST /api/stt` → auto-sends transcribed text

**🔊 Voice Output (TTS):**
- Click 🔊 on any assistant message
- Calls `POST /api/tts` → plays WAV audio
- Shows ▶️ while playing, 🔊 when stopped

---

## 🧩 Components

### 🤖 assistant-ui (8 components)

| Component | Purpose |
|-----------|---------|
| `attachment.tsx` | File/URL attachment rendering |
| `follow-up-suggestions.tsx` | Suggested follow-up questions |
| `markdown-text.tsx` | Markdown rendering in messages |
| `reasoning.tsx` | AI thinking/reasoning display |
| `thread.tsx` | Chat thread wrapper + provider |
| `tool-fallback.tsx` | Fallback UI for tool calls |
| `tool-group.tsx` | Grouped tool call display |
| `tooltip-icon-button.tsx` | Icon button with tooltip |

### 🎨 shadcn/ui (11 primitives)

| Component | File | Description |
|-----------|------|-------------|
| `Avatar` | `avatar.tsx` | User/AI avatar display |
| `Badge` | `badge.tsx` | Status badges |
| `Button` | `button.tsx` | Button (variants: default, outline, ghost, etc.) |
| `Card` | `card.tsx` | Card container (header, content, footer) |
| `Collapsible` | `collapsible.tsx` | Expandable/collapsible content |
| `Dialog` | `dialog.tsx` | Modal dialog (for add video) |
| `Input` | `input.tsx` | Text input field |
| `ScrollArea` | `scroll-area.tsx` | Custom scrollbar container |
| `Separator` | `separator.tsx` | Horizontal/vertical divider |
| `Textarea` | `textarea.tsx` | Multi-line text input |
| `Tooltip` | `tooltip.tsx` | Hover tooltip |

---

## 📚 Lib Modules

### 📡 `api.ts` — Fetch Wrapper

```typescript
// Automatic features:
✅ JWT token from localStorage → Authorization: Bearer header
✅ 401 response → clear token → redirect to /login
✅ Error parsing from backend { detail: "..." } format
✅ Base URL from NEXT_PUBLIC_BACKEND_URL (default: http://localhost:8000)
```

```typescript
// Usage
import { api } from "@/lib/api";

const data = await api("/api/auth/me");              // GET
const data = await api("/api/videos", {              // POST
  method: "POST",
  body: JSON.stringify({ url: "https://..." }),
});
```

---

### 🔐 `auth.ts` — Zustand Auth Store

```typescript
// State shape
{
  user: { id: number, username: string } | null;
  loading: boolean;
}

// Actions
login(username, password)    // POST /api/auth/login → store token
register(username, password) // POST /api/auth/register → store token
logout()                     // Clear token + user
checkAuth()                  // GET /api/auth/me → validate token
```

```typescript
// Usage
import { useAuth } from "@/lib/auth";

const { user, login, logout, loading } = useAuth();
```

---

### 🔧 `utils.ts` — cn() Helper

```typescript
// Merges Tailwind classes safely
cn("px-4 py-2", "px-8")  // → "px-8 py-2" (last wins)
cn("bg-red-500", isActive && "bg-blue-500")  // conditional
```

---

## 🎨 Styling & Theming

### Dark Mode

Dark mode is **forced** on the root `<html>` element:

```tsx
<html className="dark ...">
```

### Color System (oklch)

| Token | Dark Mode |
|-------|-----------|
| `--background` | Deep dark |
| `--foreground` | Light text |
| `--primary` | Accent color |
| `--muted` | Subtle elements |
| `--destructive` | Error red |
| `--border` | Divider lines |
| `--ring` | Focus ring |

### Fonts

```css
--font-geist-sans   /* UI text */
--font-geist-mono   /* Code blocks */
```

### Border Radius

```
--radius: 0.625rem
  sm:  calc(var(--radius) - 4px)
  md:  calc(var(--radius) - 2px)
  lg:  var(--radius)
  xl:  calc(var(--radius) + 4px)
```

---

## ⚙️ Configuration

### Environment Variables

Create `/.env.local`:

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | ❌ | `http://localhost:8000` | 🔗 Backend API URL |

```bash
# Example .env.local
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

> ⚠️ `NEXT_PUBLIC_` prefix exposes the variable to the browser.

### TypeScript Config

| Setting | Value |
|---------|-------|
| `strict` | `true` |
| `target` | `ES2017` |
| `module` | `esnext` |
| `jsx` | `react-jsx` |
| Path alias | `@/*` → `./src/*` |

### ESLint Config

Flat config format (ESLint 9) with:
- `eslint-config-next/core-web-vitals`
- `eslint-config-next/typescript`

```bash
npm run lint    # Run ESLint
```

### shadcn/ui Config

| Setting | Value |
|---------|-------|
| Style | `base-nova` |
| Base color | `neutral` |
| Icons | `lucide` |
| CSS variables | `true` |
| RSC | `true` |

---

## 🔗 Backend Integration

The frontend communicates with the **FastAPI backend** at `http://localhost:8000`.

### API Calls Made

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Pages                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📄 page.tsx (root)                                     │
│    └─ GET /api/auth/me (checkAuth)                     │
│                                                         │
│  🔑 login/page.tsx                                      │
│    └─ POST /api/auth/login                             │
│                                                         │
│  📝 register/page.tsx                                   │
│    └─ POST /api/auth/register                          │
│                                                         │
│  🎬 dashboard/page.tsx                                  │
│    ├─ GET /api/videos (list)                            │
│    ├─ POST /api/videos (add)                            │
│    └─ DELETE /api/videos/{id} (delete)                  │
│                                                         │
│  💬 chat/page.tsx                                       │
│    ├─ POST /api/ingest (pre-warm transcript)            │
│    ├─ POST /api/chat (send message)                     │
│    ├─ POST /api/stt (speech-to-text)                    │
│    └─ POST /api/tts (text-to-speech)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Auth Flow

```
Login/Register
  │
  ├─ POST /api/auth/login
  │    └─ Response: { token, username }
  │
  ├─ localStorage.setItem("token", token)
  │
  └─ All future requests:
       Authorization: Bearer {token}
```

---

## 🎤 Voice Features

### Speech-to-Text (Mic Button)

```
Click 🎤
  │
  ├─ MediaRecorder.start() (audio/webm)
  │
  ├─ Red pulse animation 🔴
  │
  ├─ Click again → stop recording
  │
  ├─ audioBlob → FormData
  │    └─ POST /api/stt
  │         └─ Response: { text: "transcribed..." }
  │
  └─ Auto-send as chat message
```

### Text-to-Speech (🔊 Button)

```
Click 🔊 on assistant message
  │
  ├─ POST /api/tts
  │    └─ Body: { text, language: "en-IN", speaker: "shubh" }
  │
  ├─ Response: audio/wav bytes
  │
  ├─ new Audio(blob) → play()
  │
  └─ Shows ▶️ while playing
     Shows 🔊 when stopped
```

### Supported Languages

| Code | Language |
|------|----------|
| `en-IN` | English |
| `hi-IN` | Hindi |
| `ta-IN` | Tamil |
| `te-IN` | Telugu |
| `bn-IN` | Bengali |
| `mr-IN` | Marathi |
| `gu-IN` | Gujarati |
| `kn-IN` | Kannada |
| `ml-IN` | Malayalam |
| `or-IN` | Odia |
| `pa-IN` | Punjabi |

---

## 📂 File Reference

| File | Lines | Description |
|------|:-----:|-------------|
| `src/app/layout.tsx` | 33 | 🏗️ Root layout (dark, Geist fonts) |
| `src/app/page.tsx` | 26 | 🔀 Auth redirector |
| `src/app/globals.css` | 130 | 🎨 Tailwind + shadcn theme |
| `src/app/login/page.tsx` | 76 | 🔑 Login form |
| `src/app/register/page.tsx` | 92 | 📝 Registration form |
| `src/app/dashboard/page.tsx` | 202 | 🎬 Video grid + CRUD |
| `src/app/chat/page.tsx` | 307 | 💬 Chat + voice I/O |
| `src/lib/api.ts` | 22 | 📡 Fetch wrapper |
| `src/lib/auth.ts` | 54 | 🔐 Zustand auth store |
| `src/lib/utils.ts` | 6 | 🔧 cn() helper |
| **Pages total** | **762** | |
| **Components** | **~2,500** | 8 assistant-ui + 11 shadcn |
| **Total src/** | **~3,300** | |

---

<div align="center">

**Built with ❤️ using Next.js 16 + React 19 + Tailwind CSS v4**

[⬆ Back to Top](#-frontend--ai-tutor)

</div>

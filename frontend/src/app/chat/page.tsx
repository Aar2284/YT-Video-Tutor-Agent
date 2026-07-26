"use client";

import { Suspense, useEffect, useRef, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

const PYTHON_BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-background"><div className="animate-pulse text-muted-foreground">Loading...</div></div>}>
      <ChatInner />
    </Suspense>
  );
}

function ChatInner() {
  const searchParams = useSearchParams();
  const videoId = searchParams.get("videoId") || "";
  const router = useRouter();
  const { user, loading: authLoading, checkAuth } = useAuth();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [initError, setInitError] = useState("");
  const [threadId] = useState(() => crypto.randomUUID());
  const [recording, setRecording] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => { checkAuth(); }, [checkAuth]);
  useEffect(() => { if (!authLoading && !user) router.replace("/login"); }, [user, authLoading, router]);

  // Pre-warm transcript on mount
  useEffect(() => {
    if (!user || !videoId) return;
    api("/api/ingest", { method: "POST", body: JSON.stringify({ video_id: videoId }) })
      .then(() => setInitializing(false))
      .catch((err) => {
        setInitError(err instanceof Error ? err.message : "Failed to load video");
        setInitializing(false);
      });
  }, [user, videoId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  useEffect(() => { if (!initializing) inputRef.current?.focus(); }, [initializing]);

  const send = useCallback(async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading || initializing) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const data = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: msg, thread_id: threadId, video_id: videoId }),
      });
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, initializing, threadId, videoId]);

  // ── STT: Mic recording ──────────────────────────────────────────────────

  async function toggleMic() {
    if (recording) {
      mediaRecorderRef.current?.stop();
      setRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const file = new File([blob], "recording.webm", { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", file);
        try {
          const token = localStorage.getItem("token");
          const res = await fetch(`${PYTHON_BACKEND}/api/stt`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
          if (res.ok) {
            const data = await res.json();
            if (data.text) send(data.text);
          }
        } catch {}
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setRecording(true);
    } catch {}
  }

  // ── TTS: Play assistant message ─────────────────────────────────────────

  // Ref to track current blob URL for cleanup
  const blobUrlRef = useRef<string | null>(null);

  function stopCurrentAudio() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
    setSpeakingIdx(null);
  }

  useEffect(() => {
    return () => stopCurrentAudio();
  }, []);

  async function playTTS(text: string, idx: number) {
    if (speakingIdx === idx) {
      stopCurrentAudio();
      return;
    }
    stopCurrentAudio();
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${PYTHON_BACKEND}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text: text.slice(0, 2500), language: "en-IN", speaker: "shubh" }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      blobUrlRef.current = url;
      const audio = new Audio(url);
      audioRef.current = audio;
      setSpeakingIdx(idx);
      audio.onended = () => {
        setSpeakingIdx(null);
        URL.revokeObjectURL(url);
        blobUrlRef.current = null;
      };
      audio.play();
    } catch {}
  }

  if (authLoading || !user) {
    return <div className="min-h-screen flex items-center justify-center bg-background"><div className="animate-pulse text-muted-foreground">Loading...</div></div>;
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border px-4 py-3 flex items-center gap-3 shrink-0">
        <button onClick={() => router.push("/dashboard")} className="text-muted-foreground hover:text-foreground transition-colors">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5" /><path d="m12 19-7-7 7-7" />
          </svg>
        </button>
        <div className="min-w-0">
          <h1 className="text-sm font-medium truncate">AI Tutor</h1>
          <p className="text-xs text-muted-foreground truncate">Video: {videoId}</p>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 && !initializing && !initError && (
            <div className="text-center py-20">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-muted mb-4">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground">
                  <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
                </svg>
              </div>
              <h2 className="text-lg font-medium mb-1">Ask anything about this video</h2>
              <p className="text-sm text-muted-foreground">Type or use the mic to ask a question</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} group`}>
              <div className={`max-w-[85%] flex items-end gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user" ? "bg-foreground text-background" : "bg-muted text-foreground"
                }`}>
                  {msg.content}
                </div>
                {msg.role === "assistant" && (
                  <button
                    onClick={() => playTTS(msg.content, i)}
                    className={`shrink-0 h-7 w-7 rounded-full flex items-center justify-center transition-colors ${
                      speakingIdx === i ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                    title={speakingIdx === i ? "Stop" : "Read aloud"}
                  >
                    {speakingIdx === i ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>
                    ) : (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                      </svg>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-2xl px-4 py-3 text-sm">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
                </span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border p-4 shrink-0">
        <div className="max-w-3xl mx-auto">
          {initError ? (
            <div className="text-center py-4">
              <p className="text-sm text-destructive mb-2">{initError}</p>
              <button onClick={() => router.push("/dashboard")} className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-4">
                Back to dashboard
              </button>
            </div>
          ) : initializing ? (
            <div className="flex items-center justify-center gap-3 py-4 text-sm text-muted-foreground">
              <div className="h-4 w-4 border-2 border-muted-foreground border-t-transparent rounded-full animate-spin" />
              Preparing transcript...
            </div>
          ) : (
            <div className="flex gap-2 items-end">
              <textarea
                ref={inputRef}
                placeholder="Ask a question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                rows={1}
                className="flex-1 resize-none rounded-xl border border-border bg-background px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring max-h-32"
              />
              {/* Mic button */}
              <button
                onClick={toggleMic}
                className={`shrink-0 h-10 w-10 rounded-xl flex items-center justify-center transition-colors ${
                  recording
                    ? "bg-destructive text-destructive-foreground animate-pulse"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
                title={recording ? "Stop recording" : "Voice input"}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" x2="12" y1="19" y2="22"/>
                </svg>
              </button>
              {/* Send button */}
              <button
                onClick={() => send()}
                disabled={loading || !input.trim()}
                className="shrink-0 h-10 w-10 rounded-xl bg-foreground text-background flex items-center justify-center hover:opacity-90 disabled:opacity-30 transition-opacity"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m5 12 7-7 7 7" /><path d="M12 19V5" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

interface Video {
  id: number;
  video_id: string;
  title: string;
  thumbnail: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user, loading: authLoading, checkAuth, logout } = useAuth();
  const router = useRouter();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [url, setUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState("");

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      api("/api/videos")
        .then(setVideos)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [user]);

  async function handleAdd() {
    if (!url.trim()) return;
    setAdding(true);
    setAddError("");
    try {
      const video = await api("/api/videos", {
        method: "POST",
        body: JSON.stringify({ url: url.trim() }),
      });
      setVideos((prev) => [video, ...prev]);
      setUrl("");
      setShowAdd(false);
      router.push(`/chat?videoId=${video.video_id}`);
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to add video");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await api(`/api/videos/${id}`, { method: "DELETE" });
      setVideos((prev) => prev.filter((v) => v.id !== id));
    } catch {}
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold">AI Tutor</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">{user.username}</span>
          <button onClick={logout} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Sign out
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Your Videos</h2>
          <button
            onClick={() => setShowAdd(true)}
            className="px-4 py-2 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-90"
          >
            + New Chat
          </button>
        </div>

        {/* Add Video Modal */}
        {showAdd && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-background border border-border rounded-xl p-6 w-full max-w-md space-y-4">
              <h3 className="text-lg font-semibold">Add YouTube Video</h3>
              <input
                type="text"
                placeholder="https://youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                autoFocus
                className="w-full px-4 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
              {addError && (
                <p className="text-sm text-destructive">{addError}</p>
              )}
              {adding && (
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <div className="h-4 w-4 border-2 border-muted-foreground border-t-transparent rounded-full animate-spin" />
                  Fetching transcript and preparing tutor...
                </div>
              )}
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => { setShowAdd(false); setUrl(""); setAddError(""); }}
                  disabled={adding}
                  className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAdd}
                  disabled={adding || !url.trim()}
                  className="px-4 py-2 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-90 disabled:opacity-50"
                >
                  {adding ? "Adding..." : "Add Video"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Video Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-xl border border-border overflow-hidden animate-pulse">
                <div className="aspect-video bg-muted" />
                <div className="p-4">
                  <div className="h-4 bg-muted rounded w-3/4" />
                </div>
              </div>
            ))}
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground mb-4">No videos yet</p>
            <button
              onClick={() => setShowAdd(true)}
              className="px-4 py-2 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-90"
            >
              Add your first video
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((video) => (
              <div
                key={video.id}
                className="group rounded-xl border border-border overflow-hidden hover:border-foreground/30 transition-colors cursor-pointer"
                onClick={() => router.push(`/chat?videoId=${video.video_id}`)}
              >
                <div className="aspect-video relative overflow-hidden bg-muted">
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                </div>
                <div className="p-4 flex items-start justify-between gap-2">
                  <h3 className="text-sm font-medium line-clamp-2">{video.title || "Untitled video"}</h3>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(video.id); }}
                    className="shrink-0 text-muted-foreground hover:text-destructive text-xs transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

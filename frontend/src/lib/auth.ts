import { create } from "zustand";
import { api } from "@/lib/api";

interface AuthState {
  user: { id: number; username: string } | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,

  login: async (username, password) => {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("token", data.token);
    set({ user: { id: data.user_id || 0, username: data.username } });
  },

  register: async (username, password) => {
    const data = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("token", data.token);
    set({ user: { id: data.user_id || 0, username: data.username } });
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null });
  },

  checkAuth: async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      set({ user: null, loading: false });
      return;
    }
    try {
      const data = await api("/api/auth/me");
      set({ user: { id: data.id, username: data.username }, loading: false });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, loading: false });
    }
  },
}));

import { useCallback, useEffect, useState } from "react";

export type Session = { id: string; name: string };

// Same storage keys as the previous UI, so existing conversations carry over.
const SESSIONS_KEY = "agentic-compliance-sessions";
const ACTIVE_KEY = "agentic-compliance-active-user-id";

const read = <T,>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
};

const write = (key: string, value: string) => {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* storage unavailable: sessions just won't persist */
  }
};

const newSession = (name: string): Session => ({ id: crypto.randomUUID(), name });

function loadInitial(): { sessions: Session[]; activeId: string } {
  let sessions = read<Session[]>(SESSIONS_KEY, []);
  if (!Array.isArray(sessions) || sessions.length === 0) sessions = [newSession("Conversation 1")];
  let activeId = "";
  try {
    activeId = localStorage.getItem(ACTIVE_KEY) ?? "";
  } catch {
    /* ignore */
  }
  if (!sessions.some((s) => s.id === activeId)) activeId = sessions[0].id;
  return { sessions, activeId };
}

export function useSessions() {
  const [{ sessions, activeId }, setState] = useState(loadInitial);

  useEffect(() => {
    write(SESSIONS_KEY, JSON.stringify(sessions));
    write(ACTIVE_KEY, activeId);
  }, [sessions, activeId]);

  const create = useCallback(() => {
    setState((state) => {
      const session = newSession(`Conversation ${state.sessions.length + 1}`);
      return { sessions: [...state.sessions, session], activeId: session.id };
    });
  }, []);

  const select = useCallback((id: string) => {
    setState((state) => (state.sessions.some((s) => s.id === id) ? { ...state, activeId: id } : state));
  }, []);

  const remove = useCallback((id: string) => {
    setState((state) => {
      let remaining = state.sessions.filter((s) => s.id !== id);
      if (remaining.length === 0) remaining = [newSession("Conversation 1")];
      const stillActive = remaining.some((s) => s.id === state.activeId);
      return { sessions: remaining, activeId: stillActive ? state.activeId : remaining[0].id };
    });
  }, []);

  return { sessions, activeId, create, select, remove };
}

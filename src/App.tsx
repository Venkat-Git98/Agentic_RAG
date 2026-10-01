import { useCallback, useEffect, useRef, useState } from "react";
import { BookOpen, ChevronDown, MessageSquareText, Moon, Plus, Sun, Trash2, Workflow } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useSessions } from "@/lib/sessions";
import { AskView, type AskHandle } from "@/views/AskView";
import { BrowseView } from "@/views/BrowseView";
import { HowItWorksView } from "@/views/HowItWorksView";

type View = "ask" | "browse" | "how";

const TABS: { id: View; label: string; icon: typeof BookOpen }[] = [
  { id: "ask", label: "Ask", icon: MessageSquareText },
  { id: "browse", label: "Browse code", icon: BookOpen },
  { id: "how", label: "How it works", icon: Workflow },
];

const DEFAULT_SECTION = "1607";

function parseHash(): { view: View; section: string } {
  const [view, section] = window.location.hash.replace(/^#\/?/, "").split("/");
  if (view === "browse") return { view, section: /^\d{3,4}(\.\d+)*$/.test(section ?? "") ? section : DEFAULT_SECTION };
  if (view === "how") return { view, section: DEFAULT_SECTION };
  return { view: "ask", section: DEFAULT_SECTION };
}

function useTheme() {
  const [dark, setDark] = useState(() => {
    try {
      const stored = localStorage.getItem("va-code-theme");
      if (stored) return stored === "dark";
    } catch {
      /* ignore */
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    document.documentElement.style.colorScheme = dark ? "dark" : "light";
  }, [dark]);
  const toggle = () =>
    setDark((value) => {
      try {
        localStorage.setItem("va-code-theme", value ? "light" : "dark");
      } catch {
        /* ignore */
      }
      return !value;
    });
  return { dark, toggle };
}

export default function App() {
  const [{ view, section }, setRoute] = useState(parseHash);
  const { sessions, activeId, create, select, remove } = useSessions();
  const { dark, toggle } = useTheme();
  const askRef = useRef<AskHandle>(null);
  const pendingQuestion = useRef<string | null>(null);

  useEffect(() => {
    const onHash = () => setRoute(parseHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = useCallback((next: View, nextSection?: string) => {
    window.location.hash = next === "browse" ? `#/browse/${nextSection ?? DEFAULT_SECTION}` : `#/${next}`;
  }, []);

  const openInBrowser = useCallback((number: string) => go("browse", number), [go]);

  const askFromBrowser = useCallback(
    (question: string) => {
      pendingQuestion.current = question;
      go("ask");
    },
    [go],
  );

  // The Ask view stays mounted, so a question queued from the code browser can be sent once it is visible.
  useEffect(() => {
    if (view === "ask" && pendingQuestion.current) {
      askRef.current?.ask(pendingQuestion.current);
      pendingQuestion.current = null;
    }
  }, [view]);

  const active = sessions.find((s) => s.id === activeId);

  return (
    <TooltipProvider>
      <div className="flex h-dvh flex-col">
        <header className="flex items-center gap-2 border-b border-border bg-card px-4 py-2 sm:gap-4">
          <a href="#/ask" className="flex items-baseline gap-1 font-display text-xl font-bold uppercase tracking-wider">
            VA <span className="text-primary">§</span> <span className="hidden min-[380px]:inline">Code Assistant</span>
          </a>

          <nav className="ml-auto hidden gap-1 md:flex" aria-label="Sections">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => go(tab.id, section)}
                aria-current={view === tab.id ? "page" : undefined}
                className={`flex items-center gap-1.5 border px-3 py-1.5 text-sm font-medium ${
                  view === tab.id ? "border-foreground bg-secondary" : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="size-4" /> {tab.label}
              </button>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-1 md:ml-2">
            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="outline" size="sm" className="max-w-40" />}>
                <span className="truncate">{active?.name ?? "Conversation"}</span>
                <ChevronDown />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem onClick={() => { create(); go("ask"); }}>
                  <Plus /> New conversation
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {sessions.map((session) => (
                  <DropdownMenuItem key={session.id} onClick={() => { select(session.id); go("ask"); }} className="justify-between">
                    <span className={`truncate ${session.id === activeId ? "font-semibold" : ""}`}>{session.name}</span>
                    <button
                      aria-label={`Delete ${session.name}`}
                      className="text-muted-foreground hover:text-redline"
                      onClick={(event) => {
                        event.stopPropagation();
                        remove(session.id);
                      }}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="ghost" size="icon" onClick={toggle} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}>
              {dark ? <Sun /> : <Moon />}
            </Button>
            <a
              href="https://github.com/Venkat-Git98/Agentic_RAG"
              target="_blank"
              rel="noreferrer"
              className="hidden px-2 text-sm text-muted-foreground hover:text-foreground sm:block"
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/svenkatesh-js/"
              target="_blank"
              rel="noreferrer"
              className="hidden px-2 text-sm text-muted-foreground hover:text-foreground sm:block"
            >
              LinkedIn
            </a>
          </div>
        </header>

        <div className="min-h-0 flex-1 pt-3">
          {/* Ask stays mounted so an answer keeps streaming while you look at another tab. */}
          <div className={view === "ask" ? "h-full" : "hidden"}>
            <AskView key={activeId} ref={askRef} sessionId={activeId} onOpenInBrowser={openInBrowser} />
          </div>
          {view === "browse" ? (
            <BrowseView number={section} onNavigate={(number) => go("browse", number)} onAsk={askFromBrowser} />
          ) : null}
          {view === "how" ? (
            <div className="h-full overflow-y-auto">
              <HowItWorksView />
            </div>
          ) : null}
        </div>

        <nav className="grid grid-cols-3 border-t border-border bg-card pb-[env(safe-area-inset-bottom)] md:hidden" aria-label="Sections">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => go(tab.id, section)}
              aria-current={view === tab.id ? "page" : undefined}
              className={`flex flex-col items-center gap-0.5 py-2 text-[0.7rem] font-medium ${
                view === tab.id ? "text-primary shadow-[inset_0_2px_0_var(--primary)]" : "text-muted-foreground"
              }`}
            >
              <tab.icon className="size-4" /> {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </TooltipProvider>
  );
}

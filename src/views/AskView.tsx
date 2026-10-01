import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";
import { useCallback, useEffect, useImperativeHandle, useMemo, useState, type Ref } from "react";
import { Check, Copy, Globe, Plus, Trash2 } from "lucide-react";

import { ChainOfThought, ChainOfThoughtContent, ChainOfThoughtHeader } from "@/components/ai-elements/chain-of-thought";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { Suggestion } from "@/components/ai-elements/suggestion";
import { RunTrace } from "@/components/app/RunTrace";
import { SourceView } from "@/components/app/SourceView";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { API, fetchHistory, fetchReferences, type AnswerMeta, type Source, type TraceEvent } from "@/lib/api";
import { idFromCiteHref, linkCitations } from "@/lib/citations";
import type { Session } from "@/lib/sessions";
import { cjk } from "@streamdown/cjk";
import { createMathPlugin } from "@streamdown/math";

// Answers write inline math as $K_{LL}$, so single-dollar math has to be enabled.
const markdownPlugins = { cjk, math: createMathPlugin({ singleDollarTextMath: true }) };

const EXAMPLES = [
  "What minimum live load applies to office floors and to corridors above the first floor?",
  "Where is an automatic sprinkler system required in Group A-2 occupancies?",
  "What does Section 1607.12 say about reducing live loads?",
  "Calculate the flat roof snow load for pg = 30 psf with Ce, Ct and Is all 1.0.",
];

const STATS = [
  { value: "33", label: "chapters indexed" },
  { value: "5,961", label: "graph nodes" },
  { value: "8,421", label: "relationships" },
];

const FEATURES = [
  { title: "Cited answers", body: "Each section and table an answer names links to its real text in the code." },
  { title: "Live run trace", body: "Watch the agents triage, plan, search and write, with timings for every step." },
  { title: "Browse the code", body: "Read any section, see what it cites and what cites it, and explore the graph." },
];

type Selected = { messageId: string; source: Source } | null;
export type AskHandle = { ask: (question: string) => void };

const textOf = (message: UIMessage) =>
  message.parts.map((part) => (part.type === "text" ? part.text : "")).join("");

function dataOf<T>(message: UIMessage, type: string): T[] {
  return message.parts.filter((part) => part.type === type).map((part) => (part as unknown as { data: T }).data);
}

function useIsWide() {
  const query = "(min-width: 1024px)";
  const [wide, setWide] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const media = window.matchMedia(query);
    const update = () => setWide(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return wide;
}

function Hero({ onAsk }: { onAsk: (q: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 py-6 sm:py-12">
      <div className="label-caps">2021 Virginia Construction Code · graph-grounded answers</div>
      <h1 className="text-balance text-4xl font-bold leading-[1.1] sm:text-5xl min-[125rem]:text-6xl">
        Ask the building code a question. See exactly where the answer came from.
      </h1>
      <p className="max-w-2xl text-muted-foreground">
        A team of AI agents plans the research, searches a knowledge graph of the code, and links every section and table
        the answer names to its actual text.
      </p>
      <div className="panel grid grid-cols-3 overflow-hidden">
        {STATS.map((stat) => (
          <div key={stat.label} className="border-l border-border px-3 py-2 first:border-l-0">
            <div className="font-mono text-xl tabular-nums">{stat.value}</div>
            <div className="text-xs text-muted-foreground">{stat.label}</div>
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <div className="label-caps">Try one</div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {EXAMPLES.map((example) => (
            <Suggestion
              key={example}
              suggestion={example}
              onClick={onAsk}
              className="h-auto justify-start whitespace-normal rounded-xl bg-card px-4 py-3 text-left shadow-xs"
            />
          ))}
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="panel flex flex-col gap-1 p-4">
            <div className="font-semibold">{feature.title}</div>
            <p className="text-sm text-muted-foreground">{feature.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Left rail on wide screens: conversations and example questions. */
function Rail({
  sessions,
  activeId,
  onNew,
  onSelect,
  onDelete,
  onAsk,
}: {
  sessions: Session[];
  activeId: string;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onAsk: (question: string) => void;
}) {
  return (
    <aside className="panel hidden min-h-0 flex-col gap-4 overflow-y-auto p-3 2xl:flex">
      <Button onClick={onNew} className="justify-start">
        <Plus /> New conversation
      </Button>
      <div className="flex flex-col gap-1">
        <div className="label-caps px-2">Conversations</div>
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`group flex items-center rounded-lg text-sm ${session.id === activeId ? "bg-secondary font-medium" : "text-muted-foreground hover:bg-muted"}`}
          >
            <button className="min-w-0 flex-1 truncate px-2 py-1.5 text-left" onClick={() => onSelect(session.id)}>
              {session.name}
            </button>
            <button
              aria-label={`Delete ${session.name}`}
              className="px-2 text-muted-foreground opacity-0 hover:text-redline focus-visible:opacity-100 group-hover:opacity-100"
              onClick={() => onDelete(session.id)}
            >
              <Trash2 className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
      <div className="mt-auto flex flex-col gap-1">
        <div className="label-caps px-2">Try asking</div>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            onClick={() => onAsk(example)}
            className="rounded-lg px-2 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {example}
          </button>
        ))}
      </div>
    </aside>
  );
}

function Answer({
  message,
  streaming,
  historySources,
  selected,
  onSelect,
}: {
  message: UIMessage;
  streaming: boolean;
  historySources?: Source[];
  selected: Selected;
  onSelect: (selected: Selected) => void;
}) {
  const [tab, setTab] = useState<"answer" | "trace">("answer");
  const [copied, setCopied] = useState(false);
  const text = textOf(message);
  const events = dataOf<TraceEvent>(message, "data-trace");
  const meta = dataOf<AnswerMeta>(message, "data-meta")[0];
  const sources = dataOf<{ sources: Source[] }>(message, "data-sources")[0]?.sources ?? historySources ?? [];
  const linked = useMemo(() => linkCitations(text, sources), [text, sources]);

  const components = useMemo(
    () => ({
      a: ({ href, children }: { href?: string; children?: React.ReactNode }) => {
        const id = idFromCiteHref(href);
        const source = id ? sources.find((s) => s.id === id) : undefined;
        if (!source) {
          return (
            <a href={href} target="_blank" rel="noreferrer" className="text-primary underline">
              {children}
            </a>
          );
        }
        const active = selected?.messageId === message.id && selected.source.id === source.id;
        return (
          <button type="button" className="cite-chip" data-active={active} onClick={() => onSelect({ messageId: message.id, source })}>
            {children}
          </button>
        );
      },
    }),
    [sources, selected, message.id, onSelect],
  );

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  if (!text) {
    // Still working: show the live trace instead of a blank bubble.
    return (
      <Message from="assistant">
        <MessageContent className="panel w-full p-4">
          <ChainOfThought defaultOpen>
            <ChainOfThoughtHeader>
              <Shimmer>{streaming ? "Working on it" : "Run trace"}</Shimmer>
            </ChainOfThoughtHeader>
            <ChainOfThoughtContent>
              <RunTrace events={events} live={streaming} />
            </ChainOfThoughtContent>
          </ChainOfThought>
        </MessageContent>
      </Message>
    );
  }

  return (
    <Message from="assistant">
      <MessageContent className="panel w-full min-w-0 gap-3 p-4">
        {events.length ? (
          <div className="seg self-start" role="tablist">
            {(["answer", "trace"] as const).map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={tab === name}
                onClick={() => setTab(name)}
              >
                {name === "trace" ? `Run trace${meta?.seconds ? ` · ${meta.seconds} s` : ""}` : "Answer"}
              </button>
            ))}
          </div>
        ) : null}

        {tab === "trace" ? (
          <RunTrace events={events} meta={meta} />
        ) : (
          <>
            <MessageResponse components={components} plugins={markdownPlugins} className="min-w-0 [&_.katex-display]:overflow-x-auto [&_pre]:overflow-x-auto">
              {linked}
            </MessageResponse>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border pt-2 text-xs text-muted-foreground">
              {sources.length ? (
                <span className="flex flex-wrap items-center gap-1.5">
                  <span>
                    {sources.length} source{sources.length === 1 ? "" : "s"} in the code graph:
                  </span>
                  {sources.map((source) => (
                    <button
                      key={source.id}
                      type="button"
                      className="cite-chip"
                      data-active={selected?.messageId === message.id && selected.source.id === source.id}
                      onClick={() => onSelect({ messageId: message.id, source })}
                    >
                      {source.label}
                    </button>
                  ))}
                </span>
              ) : (
                <span>No code sections are cited in this answer.</span>
              )}
              {meta?.web_used ? (
                <span className="inline-flex items-center gap-1 text-amber">
                  <Globe className="size-3" /> Part of this answer came from web search, not the code graph.
                </span>
              ) : null}
            </div>
          </>
        )}
      </MessageContent>
      <div>
        <Button variant="ghost" size="sm" onClick={copy} className="text-muted-foreground">
          {copied ? <Check /> : <Copy />} {copied ? "Copied" : "Copy answer"}
        </Button>
      </div>
    </Message>
  );
}

export function AskView({
  sessionId,
  sessions,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  onOpenInBrowser,
  ref,
}: {
  sessionId: string;
  sessions: Session[];
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onOpenInBrowser: (number: string) => void;
  ref?: Ref<AskHandle>;
}) {
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${API}/api/chat`,
        // The server keeps the conversation; only the newest message needs to travel.
        prepareSendMessagesRequest: ({ id, messages }) => ({ body: { id, messages: messages.slice(-1) } }),
      }),
    [],
  );
  const { messages, sendMessage, setMessages, status, stop, error } = useChat({ id: sessionId, transport });
  const [selected, setSelected] = useState<Selected>(null);
  const [historySources, setHistorySources] = useState<Record<string, Source[]>>({});
  const [loadingHistory, setLoadingHistory] = useState(true);
  const wide = useIsWide();
  const busy = status === "submitted" || status === "streaming";

  // Load the stored conversation for this session, then look up citations for past answers.
  useEffect(() => {
    let cancelled = false;
    setSelected(null);
    setLoadingHistory(true);
    fetchHistory(sessionId)
      .then((history) => {
        if (cancelled) return;
        const restored: UIMessage[] = history
          .filter((m) => (m.role === "user" || m.role === "assistant") && m.content)
          .map((m, i) => ({ id: `history-${i}`, role: m.role, parts: [{ type: "text", text: m.content }] }));
        setMessages(restored);
        restored
          .filter((m) => m.role === "assistant")
          .slice(-6)
          .forEach((m) => {
            fetchReferences(textOf(m))
              .then((sources) => !cancelled && setHistorySources((prev) => ({ ...prev, [m.id]: sources })))
              .catch(() => undefined);
          });
      })
      .catch(() => !cancelled && setMessages([]))
      .finally(() => !cancelled && setLoadingHistory(false));
    return () => {
      cancelled = true;
    };
  }, [sessionId, setMessages]);

  const ask = useCallback(
    (question: string) => {
      const text = question.trim();
      if (text && !busy) void sendMessage({ text });
    },
    [busy, sendMessage],
  );
  useImperativeHandle(ref, () => ({ ask }), [ask]);

  const last = messages[messages.length - 1];
  const waitingForFirstEvent = busy && last?.role === "user";
  const empty = messages.length === 0 && !loadingHistory;

  // The answer whose run trace the side panel shows: the one a citation was opened from, else the latest.
  const assistantMessages = messages.filter((m) => m.role === "assistant");
  const focus = assistantMessages.find((m) => m.id === selected?.messageId) ?? assistantMessages[assistantMessages.length - 1];
  const focusEvents = focus ? dataOf<TraceEvent>(focus, "data-trace") : [];
  const focusMeta = focus ? dataOf<AnswerMeta>(focus, "data-meta")[0] : undefined;

  const sourcePanel = selected ? (
    <SourceView source={selected.source} onClose={() => setSelected(null)} onOpenInBrowser={onOpenInBrowser} />
  ) : null;

  return (
    <div className="grid h-full min-h-0 w-full grid-cols-[minmax(0,1fr)] gap-4 px-4 pb-3 lg:grid-cols-[minmax(0,1fr)_minmax(22rem,26rem)] 2xl:grid-cols-[17rem_minmax(0,1.3fr)_minmax(26rem,1fr)] min-[125rem]:grid-cols-[18rem_minmax(0,1fr)_minmax(0,1.2fr)]">
      <Rail
        sessions={sessions}
        activeId={sessionId}
        onNew={onNewSession}
        onSelect={onSelectSession}
        onDelete={onDeleteSession}
        onAsk={ask}
      />
      <div className={`flex min-h-0 min-w-0 flex-col ${empty ? "lg:col-span-2" : ""}`}>
        <Conversation className="min-h-0 flex-1">
          <ConversationContent className={`mx-auto w-full px-0 ${empty ? "max-w-5xl" : "max-w-4xl"}`}>
            {empty ? <Hero onAsk={ask} /> : null}
            {messages.map((message, index) =>
              message.role === "user" ? (
                <Message from="user" key={message.id}>
                  <MessageContent>{textOf(message)}</MessageContent>
                </Message>
              ) : (
                <Answer
                  key={message.id}
                  message={message}
                  streaming={busy && index === messages.length - 1}
                  historySources={historySources[message.id]}
                  selected={selected}
                  onSelect={setSelected}
                />
              ),
            )}
            {waitingForFirstEvent ? (
              <Message from="assistant">
                <MessageContent>
                  <Shimmer>Sending your question to the agents</Shimmer>
                </MessageContent>
              </Message>
            ) : null}
            {error ? (
              <p className="border-l-2 border-redline pl-3 text-sm text-redline">
                The answer could not be completed: {error.message}. Ask again to retry.
              </p>
            ) : null}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <div className={`mx-auto w-full pt-2 ${empty ? "max-w-5xl" : "max-w-4xl"}`}>
          <PromptInput onSubmit={(message) => ask(message.text ?? "")} className="rounded-2xl bg-card shadow-[var(--shadow-soft)] [&_[data-slot=input-group]]:rounded-2xl [&_[data-slot=input-group]]:bg-card">
            <PromptInputBody>
              <PromptInputTextarea placeholder="Ask about loads, egress, fire ratings, a section number…" />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools>
                <span className="px-1 text-xs text-muted-foreground">Guidance only. Confirm with a licensed professional.</span>
              </PromptInputTools>
              <PromptInputSubmit status={status} onStop={stop} />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </div>

      {wide ? (
        empty ? null : (
          <div className="hidden min-h-0 gap-4 lg:grid min-[125rem]:grid-cols-2">
            <aside className="panel min-h-0 p-5">
              {sourcePanel ?? (
                <div className="flex h-full flex-col justify-center gap-2 text-sm text-muted-foreground">
                  <div className="label-caps">Source</div>
                  <p>
                    Click a citation such as <span className="cite-chip pointer-events-none">Table 1607.1</span> in an answer to read the
                    code text it came from.
                  </p>
                </div>
              )}
            </aside>
            {/* On very wide screens the run trace sits beside the source instead of behind a tab. */}
            <aside className="panel hidden min-h-0 flex-col gap-3 overflow-y-auto p-5 min-[125rem]:flex">
              <div className="label-caps">Run trace</div>
              <RunTrace events={focusEvents} meta={focusMeta} live={busy} />
            </aside>
          </div>
        )
      ) : (
        <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
          <DialogContent className="flex max-h-[85dvh] flex-col">
            <DialogTitle className="sr-only">Source</DialogTitle>
            {selected ? <SourceView source={selected.source} onOpenInBrowser={onOpenInBrowser} /> : null}
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

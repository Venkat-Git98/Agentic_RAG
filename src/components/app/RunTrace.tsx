import type { AnswerMeta, TraceEvent } from "@/lib/api";
import { CheckCircle2, CircleAlert, Globe, LoaderCircle } from "lucide-react";

const AGENTS: Record<string, { name: string; does: string }> = {
  TriageAgent: { name: "Triage", does: "Decides how the question should be handled" },
  ContextualAnsweringAgent: { name: "Follow-up", does: "Tries to answer from the conversation so far" },
  PlanningAgent: { name: "Planner", does: "Breaks the question into research steps" },
  HydeAgent: { name: "Drafts", does: "Writes a draft passage per step to guide the search" },
  ResearchOrchestrator: { name: "Research", does: "Searches the code graph for each step" },
  SynthesisAgent: { name: "Writer", does: "Writes the answer from what was found" },
  EnhancedSynthesisAgent: { name: "Writer", does: "Writes the answer from what was found" },
  MemoryAgent: { name: "Memory", does: "Saves the exchange" },
  ErrorHandler: { name: "Recovery", does: "Handles a failed step" },
};

const ROUTES: Record<string, string> = {
  simple_response: "Greeting or small talk: reply directly",
  contextual_clarification: "Follow-up: answer from the conversation",
  direct_retrieval: "Direct lookup: fetch one specific provision",
  complex_research: "Complex: plan, research in parallel, then write",
  clarify_and_rewrite: "Rewrite the question, then research",
};

const seconds = (ms?: number) => (ms == null ? "" : `${(ms / 1000).toFixed(1)} s`);

function Detail({ event }: { event: TraceEvent }) {
  const d = event.detail ?? {};
  if (event.status === "error") return <p className="text-redline">{d.error ?? "This step failed."}</p>;
  if (event.agent === "TriageAgent") {
    return (
      <>
        {d.route ? <p className="font-medium">{ROUTES[d.route] ?? d.route}</p> : null}
        {d.reason ? <p className="text-muted-foreground">{d.reason}</p> : null}
      </>
    );
  }
  if (event.agent === "PlanningAgent" && d.sub_questions?.length) {
    return (
      <ol className="list-decimal space-y-1 pl-4 text-muted-foreground">
        {d.sub_questions.map((q, i) => (
          <li key={i}>{q}</li>
        ))}
      </ol>
    );
  }
  if (event.agent === "HydeAgent" && d.documents) {
    return <p className="text-muted-foreground">{d.documents} draft passage{d.documents === 1 ? "" : "s"} written</p>;
  }
  if (event.agent === "ResearchOrchestrator" && d.searches?.length) {
    return (
      <ul className="space-y-1.5">
        {d.searches.map((s, i) => (
          <li key={i} className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span
              className={`inline-flex items-center gap-1 rounded-sm border px-1.5 font-mono text-[0.7rem] ${
                s.method === "web search" ? "border-amber text-amber" : "border-primary text-primary"
              }`}
            >
              {s.method === "web search" ? <Globe className="size-3" /> : null}
              {s.method}
            </span>
            <span className="min-w-0 flex-1 text-muted-foreground">{s.question}</span>
          </li>
        ))}
      </ul>
    );
  }
  if (event.agent === "ContextualAnsweringAgent") {
    return (
      <p className="text-muted-foreground">
        {d.answered_from_conversation ? "Answered from the conversation" : "Not enough in the conversation, so it went to research"}
      </p>
    );
  }
  if ((event.agent === "SynthesisAgent" || event.agent === "EnhancedSynthesisAgent") && d.answer_chars) {
    return (
      <p className="text-muted-foreground">
        {d.answer_chars.toLocaleString()} characters{d.calculation ? ", with a worked calculation" : ""}
      </p>
    );
  }
  return null;
}

/** What the agents actually did for one answer, from the server's trace events. */
export function RunTrace({ events, meta, live }: { events: TraceEvent[]; meta?: AnswerMeta; live?: boolean }) {
  const total = events.reduce((sum, e) => sum + (e.ms ?? 0), 0) || 1;
  if (!events.length) {
    return <p className="text-sm text-muted-foreground">{live ? "Starting…" : "No trace was recorded for this answer."}</p>;
  }
  return (
    <div className="flex flex-col gap-3 text-sm">
      <ol className="flex flex-col">
        {events.map((event, i) => {
          const agent = AGENTS[event.agent] ?? { name: event.agent, does: "" };
          const working = event.status === "start";
          return (
            <li key={i} className="grid grid-cols-[1.25rem_1fr_auto] gap-x-3 pb-4 last:pb-0">
              <div className="relative flex justify-center">
                {working ? (
                  <LoaderCircle className="size-4 animate-spin text-primary" />
                ) : event.status === "error" ? (
                  <CircleAlert className="size-4 text-redline" />
                ) : (
                  <CheckCircle2 className="size-4 text-primary" />
                )}
                {i < events.length - 1 ? <span className="absolute top-5 bottom-[-0.9rem] w-px bg-border" /> : null}
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-display text-base font-semibold uppercase tracking-wide">{agent.name}</span>
                  <span className="text-xs text-muted-foreground">{agent.does}</span>
                </div>
                <div className="mt-1 flex flex-col gap-1">{working ? null : <Detail event={event} />}</div>
                {!working && event.ms ? (
                  <div className="mt-2 h-1 bg-primary/70" style={{ width: `${Math.max(2, (event.ms / total) * 100)}%` }} />
                ) : null}
              </div>
              <span className="font-mono text-xs tabular-nums text-muted-foreground">{working ? "working" : seconds(event.ms)}</span>
            </li>
          );
        })}
      </ol>
      {meta?.seconds != null ? (
        <p className="border-t border-border pt-2 font-mono text-xs text-muted-foreground">
          Total {meta.seconds} s{meta.web_used ? " · web search used for part of this answer" : " · answered from the code graph"}
        </p>
      ) : null}
    </div>
  );
}

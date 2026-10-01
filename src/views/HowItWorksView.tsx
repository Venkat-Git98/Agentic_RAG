import { ArrowDown, ArrowRight, Database, Globe } from "lucide-react";
import type { ReactNode } from "react";

import flowchart from "@/assets/architectural-diagram.jpg";

function Box({ title, tag, children, tone = "default" }: { title: string; tag?: string; children?: ReactNode; tone?: "default" | "store" | "io" }) {
  const toneClass = tone === "store" ? "border-amber/50" : tone === "io" ? "border-primary/40 !bg-secondary" : "";
  return (
    <div className={`panel flex min-w-0 flex-col gap-1 p-4 ${toneClass}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-2">
        <h3 className="text-base font-semibold leading-tight">{title}</h3>
        {tag ? <span className="font-mono text-[0.7rem] text-muted-foreground">{tag}</span> : null}
      </div>
      {children ? <div className="text-sm text-muted-foreground">{children}</div> : null}
    </div>
  );
}

const Down = () => <ArrowDown className="mx-auto size-5 text-muted-foreground" aria-hidden />;

const ROUTES = [
  { name: "Greeting", then: "Replies directly. No research." },
  { name: "Follow-up", then: "Answers from the conversation. Falls through to research if that isn’t enough." },
  { name: "Direct lookup", then: "One specific provision. Goes straight to research." },
  { name: "Complex", then: "Planner splits it into steps, researched in parallel." },
];

const SEARCH_ORDER = ["Section lookup", "Vector search", "Keyword search", "Web search"];

const GRAPH = [
  ["Chapters", "33"],
  ["Sections", "317"],
  ["Subsections", "1,953"],
  ["Text passages", "3,405"],
  ["Tables", "118"],
  ["Equations", "69"],
  ["Diagrams", "49"],
  ["Standards", "17"],
];

const STACK = [
  ["Agents", "LangGraph state machine, Python, FastAPI"],
  ["Models", "Gemini Pro for planning and writing, Gemini Flash for triage and relevance checks"],
  ["Embeddings", "gemini-embedding-001, 768 dimensions"],
  ["Knowledge graph", "Neo4j Aura with vector and full-text indexes"],
  ["Memory", "Redis for conversation history and an answer cache"],
  ["Interface", "React 19, Vite, Tailwind, Vercel AI SDK and AI Elements"],
  ["Hosting", "Railway (API and Redis), Netlify (this site)"],
];

export function HowItWorksView() {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-10 px-4 pb-12 min-[106rem]:max-w-[140rem] min-[106rem]:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] min-[106rem]:items-start">
      <header className="flex flex-col gap-2 pt-2 min-[106rem]:col-span-2">
        <div className="label-caps">Architecture</div>
        <h1 className="text-balance text-4xl font-bold leading-[1.1]">How a question becomes a cited answer</h1>
        <p className="max-w-2xl text-muted-foreground">
          This is the workflow that runs for every question. The run trace on each answer shows these same steps with real
          timings.
        </p>
      </header>

      <section className="flex flex-col gap-3" aria-label="Request pipeline">
        <Box title="Your question" tone="io">Sent to the API with the conversation id.</Box>
        <Down />
        <Box title="Triage" tag="Gemini Flash">Reads the question and the conversation, then picks one of four routes.</Box>
        <Down />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {ROUTES.map((route) => (
            <Box key={route.name} title={route.name}>
              {route.then}
            </Box>
          ))}
        </div>
        <Down />
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_1.4fr] lg:items-stretch">
          <Box title="Planner" tag="Gemini Pro · complex route only">
            Breaks the question into two to four research steps and flags whether a calculation is needed.
          </Box>
          <ArrowRight className="hidden size-5 self-center text-muted-foreground lg:block" aria-hidden />
          <Box title="Research" tag="one search per step, in parallel">
            <p>Each step tries these in order and stops at the first result that passes a relevance check:</p>
            <ol className="mt-2 flex flex-wrap items-center gap-1.5">
              {SEARCH_ORDER.map((name, i) => (
                <li key={name} className="flex items-center gap-1.5">
                  <span
                    className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-xs ${
                      name === "Web search" ? "border-amber text-amber" : "border-primary text-primary"
                    }`}
                  >
                    {name === "Web search" ? <Globe className="size-3" /> : null}
                    {name}
                  </span>
                  {i < SEARCH_ORDER.length - 1 ? <ArrowRight className="size-3 text-muted-foreground" aria-hidden /> : null}
                </li>
              ))}
            </ol>
          </Box>
        </div>
        <Down />
        <div className="grid gap-3 sm:grid-cols-2">
          <Box title="Knowledge graph" tag="Neo4j Aura" tone="store">
            <span className="inline-flex items-center gap-1">
              <Database className="size-3.5" /> The code as chapters, sections, passages, tables and equations, with vector and
              full-text indexes.
            </span>
          </Box>
          <Box title="Conversation memory" tag="Redis" tone="store">
            <span className="inline-flex items-center gap-1">
              <Database className="size-3.5" /> History per conversation, plus a cache of answered questions.
            </span>
          </Box>
        </div>
        <Down />
        <Box title="Writer" tag="Gemini Pro">Writes the answer from what research found. Runs the numbers when the planner asked for a calculation.</Box>
        <Down />
        <Box title="Citation check" tag="graph lookup, no model">
          Every section and table number in the answer is looked up in the graph. The ones that exist become clickable
          citations with their real text.
        </Box>
        <Down />
        <Box title="Answer, sources and run trace" tone="io">Streamed to this interface in the AI SDK message format.</Box>
      </section>

      <div className="flex min-w-0 flex-col gap-10">
      <section className="grid gap-8 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <div className="label-caps">What is in the graph</div>
          <table className="w-full border-collapse text-sm">
            <tbody>
              {GRAPH.map(([name, count]) => (
                <tr key={name} className="border-b border-border">
                  <td className="py-1.5">{name}</td>
                  <td className="py-1.5 text-right font-mono tabular-nums">{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-muted-foreground">5,961 nodes and 8,421 relationships. 3,572 passages, tables and diagrams are embedded for semantic search.</p>
        </div>
        <div className="flex flex-col gap-2">
          <div className="label-caps">Built with</div>
          <dl className="text-sm">
            {STACK.map(([name, value]) => (
              <div key={name} className="grid grid-cols-[8.5rem_1fr] gap-2 border-b border-border py-1.5">
                <dt className="font-medium">{name}</dt>
                <dd className="text-muted-foreground">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="flex flex-col gap-2">
        <div className="label-caps">Original design flowchart</div>
        <p className="max-w-2xl text-sm text-muted-foreground">
          The detailed decision flowchart drawn while designing the research and retry logic. Open it full size to read the
          labels.
        </p>
        <a href={flowchart} target="_blank" rel="noreferrer" className="panel block overflow-hidden !bg-white p-3">
          <img src={flowchart} alt="Detailed flowchart of the triage, research orchestrator and synthesis decision logic" className="mx-auto max-h-[36rem] w-auto max-w-full" />
        </a>
      </section>
      </div>
    </div>
  );
}

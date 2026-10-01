export const API: string = import.meta.env.VITE_API_URL ?? "https://agenticrag-production.up.railway.app";

export type Source = {
  id: string; // "section:1607.12" | "table:1607.1"
  kind: "section" | "table";
  number: string;
  label: string;
  title: string;
  breadcrumb: string;
  text?: string;
  truncated?: boolean;
  exact: boolean;
  found_in?: string;
  table?: { headers: string[]; rows: string[][] };
};

export type TraceSearch = { question: string; method: string; relevant: boolean; context_chars: number };

export type TraceEvent = {
  agent: string;
  status: "start" | "done" | "error";
  ms?: number;
  detail?: {
    route?: string;
    reason?: string;
    sub_questions?: string[];
    calculation?: boolean;
    documents?: number;
    searches?: TraceSearch[];
    answered_from_conversation?: boolean;
    answer_chars?: number;
    cache_hit?: boolean;
    error?: string;
  };
};

export type AnswerMeta = { seconds?: number; route?: string | null; web_used?: boolean };

export type TocChapter = { number: string; title: string; sections: { number: string; title: string }[] };

export type SectionPage = {
  number: string;
  title: string;
  kind: string;
  breadcrumb: string;
  parent: string | null;
  text: string;
  children: { number: string; title: string }[];
  tables: { number: string; title: string; headers: string[]; rows: string[][] }[];
  equations: string[];
  diagrams: string[];
  standards: string[];
  cites: { id: string; kind: "section" | "table"; number: string; label: string; title: string }[];
  cited_by: { number: string; label: string; title: string }[];
};

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* keep the status code */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const fetchToc = () => getJson<{ chapters: TocChapter[] }>("/api/toc").then((d) => d.chapters);

export const fetchSection = (number: string) => getJson<SectionPage>(`/api/section/${encodeURIComponent(number)}`);

export const fetchReferences = (text: string) =>
  getJson<{ sources: Source[] }>("/api/references", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then((d) => d.sources);

export type HistoryMessage = { role: "user" | "assistant"; content: string };

export const fetchHistory = (sessionId: string) =>
  getJson<{ data: HistoryMessage[] }>(`/history?userId=${encodeURIComponent(sessionId)}`).then((d) => d.data ?? []);

export type GraphData = {
  nodes: { id: string; type: string; data: { label: string } }[];
  edges: { id: string; source: string; target: string; label: string }[];
};

export const fetchGraph = (query: string) => getJson<GraphData>(`/api/knowledge-graph?query=${encodeURIComponent(query)}`);

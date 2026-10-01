import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, CornerLeftUp, List, MessageSquareText, Share2 } from "lucide-react";

import type { GraphEdge, GraphNode } from "@/components/app/GraphCanvas";
import { CodeTable, SourceView } from "@/components/app/SourceView";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { fetchGraph, fetchReferences, fetchSection, fetchToc, type SectionPage, type Source, type TocChapter } from "@/lib/api";
import { idFromCiteHref, linkCitations } from "@/lib/citations";

// The graph library is large, so it loads only when the graph view is opened.
const GraphCanvas = lazy(() => import("@/components/app/GraphCanvas").then((m) => ({ default: m.GraphCanvas })));

const chapterOf = (number: string) => {
  const head = number.split(".")[0];
  return head.length > 2 ? head.slice(0, -2) : head;
};

/** Code text with every verified reference turned into a clickable chip. */
function LinkedText({ text, cites, onCite }: { text: string; cites: SectionPage["cites"]; onCite: (id: string) => void }) {
  const nodes = useMemo(() => {
    const linked = linkCitations(text, cites);
    const out: ReactNode[] = [];
    const pattern = /\[([^\]]+)\]\((#cite-[^)]+)\)/g;
    let cursor = 0;
    for (const match of linked.matchAll(pattern)) {
      const id = idFromCiteHref(match[2]);
      out.push(linked.slice(cursor, match.index));
      out.push(
        id ? (
          <button key={match.index} type="button" className="cite-chip" onClick={() => onCite(id)}>
            {match[1]}
          </button>
        ) : (
          match[0]
        ),
      );
      cursor = (match.index ?? 0) + match[0].length;
    }
    out.push(linked.slice(cursor));
    return out;
  }, [text, cites, onCite]);
  return <p className="code-text max-w-[70ch]">{nodes}</p>;
}

function Tree({
  toc,
  current,
  page,
  onNavigate,
}: {
  toc: TocChapter[];
  current: string;
  page: SectionPage | null;
  onNavigate: (number: string) => void;
}) {
  const [open, setOpen] = useState<Set<string>>(() => new Set([chapterOf(current)]));
  useEffect(() => setOpen((prev) => new Set(prev).add(chapterOf(current))), [current]);
  const currentSection = current.split(".")[0];
  const toggle = (number: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(number)) next.delete(number);
      else next.add(number);
      return next;
    });

  return (
    <nav aria-label="Code contents" className="font-mono text-xs leading-7">
      {toc.map((chapter) => (
        <div key={chapter.number}>
          <button type="button" onClick={() => toggle(chapter.number)} className="flex w-full items-center gap-1 truncate text-left hover:text-primary">
            {open.has(chapter.number) ? <ChevronDown className="size-3 shrink-0" /> : <ChevronRight className="size-3 shrink-0" />}
            <span className="truncate">
              {chapter.number} {chapter.title}
            </span>
          </button>
          {open.has(chapter.number) ? (
            chapter.sections.length ? (
              chapter.sections.map((section) => (
                <div key={section.number}>
                  <button
                    type="button"
                    onClick={() => onNavigate(section.number)}
                    className={`block w-full truncate border-l-2 pl-4 text-left hover:text-primary ${
                      section.number === current ? "border-primary bg-secondary" : "border-transparent"
                    }`}
                  >
                    {section.number} {section.title}
                  </button>
                  {section.number === currentSection && page && current !== section.number ? (
                    <div className="truncate border-l-2 border-primary bg-secondary pl-8">
                      {page.number} {page.title}
                    </div>
                  ) : null}
                </div>
              ))
            ) : (
              <div className="pl-4 text-muted-foreground">Not in the graph yet</div>
            )
          ) : null}
        </div>
      ))}
    </nav>
  );
}

function GraphPanel({ number, onNavigate }: { number: string; onNavigate: (number: string) => void }) {
  const [data, setData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    fetchGraph(number)
      .then((graph) => {
        if (cancelled) return;
        setData({
          nodes: graph.nodes.map((node) => ({
            id: String(node.id),
            label: node.id,
            group: node.type,
            title: `${node.type} ${node.id}${node.data?.label && node.data.label !== node.id ? `: ${node.data.label}` : ""}`,
          })),
          edges: graph.edges.map((edge) => ({ id: edge.id, from: edge.source, to: edge.target, label: edge.label, arrows: "to" })),
        });
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [number]);

  const handleClick = useMemo(
    () => (node: GraphNode) => {
      if ((node.group === "Section" || node.group === "Subsection") && node.id !== number) onNavigate(node.id);
    },
    [number, onNavigate],
  );

  if (error) return <p className="text-sm text-redline">The graph could not be loaded: {error}</p>;
  if (!data) return <p className="text-sm text-muted-foreground">Loading graph…</p>;
  return (
    <div className="flex h-full min-h-[24rem] flex-col gap-2">
      <p className="text-xs text-muted-foreground">
        Everything in the graph under {number}. Large dots are sections, small grey dots are text passages, green are tables.
        Click a section to open it.
      </p>
      <div className="min-h-0 flex-1 border border-border bg-background">
        <Suspense fallback={<p className="p-3 text-sm text-muted-foreground">Loading graph…</p>}>
          <GraphCanvas nodes={data.nodes} edges={data.edges} onNodeClick={handleClick} />
        </Suspense>
      </div>
    </div>
  );
}

export function BrowseView({
  number,
  onNavigate,
  onAsk,
}: {
  number: string;
  onNavigate: (number: string) => void;
  onAsk: (question: string) => void;
}) {
  const [toc, setToc] = useState<TocChapter[]>([]);
  const [page, setPage] = useState<SectionPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"text" | "graph">("text");
  const [contentsOpen, setContentsOpen] = useState(false);
  const [tableSource, setTableSource] = useState<Source | null>(null);

  useEffect(() => {
    fetchToc().then(setToc).catch(() => setToc([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    fetchSection(number)
      .then((data) => !cancelled && setPage(data))
      .catch((e: Error) => {
        if (!cancelled) {
          setPage(null);
          setError(e.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [number]);

  const openCitation = useMemo(
    () => (id: string) => {
      const [kind, target] = id.split(":");
      if (kind === "section") {
        onNavigate(target);
        return;
      }
      fetchReferences(`Table ${target}`)
        .then((sources) => setTableSource(sources.find((s) => s.id === id) ?? null))
        .catch(() => undefined);
    },
    [onNavigate],
  );

  const navigate = (target: string) => {
    setContentsOpen(false);
    onNavigate(target);
  };

  return (
    <div className="mx-auto grid h-full min-h-0 w-full max-w-7xl grid-cols-[minmax(0,1fr)] gap-4 px-4 pb-3 lg:grid-cols-[15rem_minmax(0,1fr)_17rem]">
      <aside className={`min-h-0 overflow-y-auto border border-border bg-card p-3 ${contentsOpen ? "block max-h-[50dvh]" : "hidden"} lg:block lg:max-h-none`}>
        <Tree toc={toc} current={number} page={page} onNavigate={navigate} />
      </aside>

      <main className="flex min-h-0 flex-col gap-3 overflow-y-auto border border-border bg-card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setContentsOpen((v) => !v)}>
            <List /> Contents
          </Button>
          {page?.parent ? (
            <Button variant="ghost" size="sm" onClick={() => onNavigate(page.parent!)}>
              <CornerLeftUp /> §{page.parent}
            </Button>
          ) : null}
          <div className="ml-auto flex gap-1 text-xs">
            {(["text", "graph"] as const).map((name) => (
              <button
                key={name}
                onClick={() => setMode(name)}
                className={`border px-2.5 py-1 font-medium ${mode === name ? "border-foreground bg-secondary" : "border-transparent text-muted-foreground"}`}
              >
                {name === "text" ? "Code text" : "Graph"}
              </button>
            ))}
          </div>
        </div>

        {error ? (
          <p className="text-sm text-redline">Section {number} could not be opened: {error}</p>
        ) : !page ? (
          <p className="text-sm text-muted-foreground">Loading §{number}…</p>
        ) : mode === "graph" ? (
          <GraphPanel number={number} onNavigate={onNavigate} />
        ) : (
          <>
            <div>
              <div className="font-mono text-xs text-muted-foreground">{page.breadcrumb}</div>
              <h2 className="text-2xl font-semibold uppercase">
                §{page.number} · {page.title}
              </h2>
            </div>
            {page.text ? (
              <LinkedText text={page.text} cites={page.cites} onCite={openCitation} />
            ) : (
              <p className="text-sm text-muted-foreground">This heading has no text of its own. Open one of its parts below.</p>
            )}
            {page.equations.length ? (
              <div className="flex flex-col gap-1 border border-border bg-background p-3">
                <div className="label-caps">Equations in this section</div>
                {page.equations.map((equation, i) => (
                  <code key={i} className="overflow-x-auto font-mono text-sm">
                    {equation}
                  </code>
                ))}
              </div>
            ) : null}
            {page.tables.map((table) => (
              <div key={table.number} className="flex flex-col gap-1">
                <div className="label-caps">Table {table.number}</div>
                <CodeTable headers={table.headers} rows={table.rows} />
              </div>
            ))}
            {page.children.length ? (
              <div className="flex flex-col gap-1">
                <div className="label-caps">Parts of this section</div>
                <ul className="grid gap-x-4 sm:grid-cols-2">
                  {page.children.map((child) => (
                    <li key={child.number}>
                      <button onClick={() => onNavigate(child.number)} className="w-full truncate py-0.5 text-left text-sm hover:text-primary">
                        <span className="font-mono text-xs">{child.number}</span> {child.title}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="mt-auto flex flex-wrap gap-2 pt-2">
              <Button size="sm" onClick={() => onAsk(`What does Section ${page.number} require?`)}>
                <MessageSquareText /> Ask about this section
              </Button>
              <Button variant="outline" size="sm" onClick={() => setMode("graph")}>
                <Share2 /> Show in graph
              </Button>
            </div>
          </>
        )}
      </main>

      <aside className="hidden min-h-0 flex-col gap-4 overflow-y-auto border border-border bg-card p-4 text-sm lg:flex">
        <div className="flex flex-col gap-1.5">
          <div className="label-caps">This section cites</div>
          {page?.cites.length ? (
            <div className="flex flex-wrap gap-1.5">
              {page.cites.map((cite) => (
                <button key={cite.id} className="cite-chip" title={cite.title} onClick={() => openCitation(cite.id)}>
                  {cite.label}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No other sections or tables.</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="label-caps">Cited by</div>
          {page?.cited_by.length ? (
            <div className="flex flex-wrap gap-1.5">
              {page.cited_by.map((cite) => (
                <button key={cite.number} className="cite-chip" title={cite.title} onClick={() => onNavigate(cite.number)}>
                  {cite.label}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No other section names this one.</p>
          )}
        </div>
        {page?.standards.length ? (
          <div className="flex flex-col gap-1.5">
            <div className="label-caps">Standards referenced</div>
            <p className="font-mono text-xs">{page.standards.join(" · ")}</p>
          </div>
        ) : null}
        <p className="mt-auto text-xs text-muted-foreground">
          Links are found by reading each section’s text for section and table numbers and checking them against the graph.
        </p>
      </aside>

      <Dialog open={Boolean(tableSource)} onOpenChange={(open) => !open && setTableSource(null)}>
        <DialogContent className="flex max-h-[85dvh] flex-col sm:max-w-2xl">
          <DialogTitle className="sr-only">Table</DialogTitle>
          {tableSource ? <SourceView source={tableSource} onOpenInBrowser={(n) => { setTableSource(null); onNavigate(n); }} /> : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

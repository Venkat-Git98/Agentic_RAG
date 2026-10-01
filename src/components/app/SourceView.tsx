import type { Source } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { BookOpen, X } from "lucide-react";

export function CodeTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  if (!rows.length) return <p className="text-sm text-muted-foreground">This table has no rows in the knowledge graph.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="border border-border bg-muted px-2 py-1 text-left font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, c) => (
                <td key={c} className="border border-border px-2 py-1 align-top tabular-nums">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** The code text behind one citation: a section excerpt or a table. */
export function SourceView({
  source,
  onClose,
  onOpenInBrowser,
}: {
  source: Source;
  onClose?: () => void;
  onOpenInBrowser: (number: string) => void;
}) {
  const browseTarget = source.kind === "table" ? source.number.split("(")[0].split(".")[0] : (source.found_in ?? source.number);
  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="label-caps">Source · from the code graph</div>
          <h3 className="text-xl font-semibold uppercase leading-tight">
            {source.label}
            {source.title ? <span className="font-medium normal-case"> · {source.title}</span> : null}
          </h3>
          <div className="font-mono text-xs text-muted-foreground">{source.breadcrumb}</div>
        </div>
        {onClose ? (
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close source">
            <X />
          </Button>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto pr-1 text-sm">
        {source.kind === "table" && source.table ? (
          <CodeTable headers={source.table.headers} rows={source.table.rows} />
        ) : (
          <>
            {!source.exact ? (
              <p className="mb-2 border-l-2 border-amber pl-2 text-xs text-muted-foreground">
                {source.label} has no entry of its own in the graph. This excerpt is where it appears inside §{source.found_in}.
              </p>
            ) : null}
            <p className="code-text">
              {source.text}
              {source.truncated ? " …" : ""}
            </p>
          </>
        )}
      </div>

      <div>
        <Button variant="outline" size="sm" onClick={() => onOpenInBrowser(browseTarget)}>
          <BookOpen /> Open in code browser
        </Button>
      </div>
    </div>
  );
}

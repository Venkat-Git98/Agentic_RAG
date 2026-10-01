import type { Source } from "./api";

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** The anchor a citation chip links to, e.g. "#cite-table-1607.1". */
export const citeHref = (id: string) => `#cite-${id.replace(":", "-")}`;

export const idFromCiteHref = (href: string | undefined) => {
  if (!href?.startsWith("#cite-")) return null;
  const rest = href.slice("#cite-".length);
  const dash = rest.indexOf("-");
  return dash < 0 ? null : `${rest.slice(0, dash)}:${rest.slice(dash + 1)}`;
};

/**
 * Turns every mention of a verified source in markdown text into a link to that
 * source ("Table 1607.1" -> [Table 1607.1](#cite-table-1607.1)). Only numbers the
 * backend found in the knowledge graph are linked; everything else stays plain text.
 */
export function linkCitations(markdown: string, sources: Pick<Source, "id" | "kind" | "number">[]): string {
  if (!sources.length) return markdown;
  const byLength = (a: string, b: string) => b.length - a.length;
  const tables = sources.filter((s) => s.kind === "table").map((s) => s.number).sort(byLength);
  const sections = sources.filter((s) => s.kind === "section").map((s) => s.number).sort(byLength);

  const alternatives: string[] = [];
  if (tables.length) alternatives.push(`(?<table>Table\\s+(?:${tables.map(escapeRegex).join("|")}))(?![\\d(]|\\.\\d)`);
  if (sections.length) {
    alternatives.push(
      `(?<section>(?:Sections?\\s+|§\\s*)?(?<![\\d.])(?:${sections.map(escapeRegex).join("|")}))(?!\\d|\\.\\d)`,
    );
  }
  if (!alternatives.length) return markdown;
  // Skip existing markdown links and code spans so nothing is linked twice.
  const pattern = new RegExp(`\\[[^\\]]*\\]\\([^)]*\\)|\`[^\`]*\`|${alternatives.join("|")}`, "g");

  return markdown.replace(pattern, (match, ...args) => {
    const groups = args[args.length - 1] as Record<string, string | undefined>;
    if (groups.table) {
      const number = groups.table.replace(/^Table\s+/, "");
      return `[${match}](${citeHref(`table:${number}`)})`;
    }
    if (groups.section) {
      const number = groups.section.replace(/^(?:Sections?\s+|§\s*)/, "");
      const label = /^\d/.test(match) ? `§${match}` : match;
      return `[${label}](${citeHref(`section:${number}`)})`;
    }
    return match;
  });
}

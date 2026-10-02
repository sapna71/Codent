"use client";

import { ExternalLink, Code2 } from "lucide-react";
import type { Source } from "@/lib/api";

export default function CitationChip({ source, onView }: { source: Source; onView?: (source: Source) => void }) {
  const isOverview = source.kind === "overview";
  const label = isOverview ? "Repository overview" : `${source.file}:${source.start_line}-${source.end_line}`;

  return (
    <div className="group inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 py-1 pl-2.5 pr-1 text-xs text-zinc-300 transition hover:border-indigo-400/40 hover:bg-indigo-500/10">
      <button onClick={() => onView?.(source)} disabled={!onView} className="flex items-center gap-1.5 disabled:cursor-default" title={onView ? "View code" : undefined}>
        <span className="font-mono text-indigo-400">[{source.ref}]</span>
        <span className="max-w-[200px] truncate">{label}</span>
        {onView && <Code2 size={11} className="text-zinc-500 group-hover:text-indigo-300" />}
      </button>
      <a href={source.github_url} target="_blank" rel="noopener noreferrer" title="Open on GitHub" className="rounded p-1 text-zinc-600 transition hover:bg-white/10 hover:text-zinc-300">
        <ExternalLink size={11} />
      </a>
    </div>
  );
}

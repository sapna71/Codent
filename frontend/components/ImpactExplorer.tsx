"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Loader2, AlertCircle, GitBranch, ChevronRight } from "lucide-react";
import { getImpact, ApiError, type IngestResult, type ImpactEntry } from "@/lib/api";

const DEPTH_COLORS = ["#6366f1", "#a855f7", "#ec4899", "#f59e0b"];

export default function ImpactExplorer({ repo }: { repo: IngestResult }) {
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rootFile, setRootFile] = useState<string | null>(null);
  const [entries, setEntries] = useState<ImpactEntry[]>([]);
  const [selected, setSelected] = useState<ImpactEntry | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!filePath.trim() || loading) return;
    setLoading(true);
    setError("");
    setSelected(null);
    try {
      const res = await getImpact(repo.repo_key, filePath.trim(), 2);
      setRootFile(res.file);
      setEntries(res.affected_files);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the backend.");
      setEntries([]);
      setRootFile(null);
    } finally {
      setLoading(false);
    }
  }

  // Position nodes on concentric rings by depth, spread evenly within each ring.
  const byDepth = new Map<number, ImpactEntry[]>();
  for (const e of entries) {
    if (!byDepth.has(e.depth)) byDepth.set(e.depth, []);
    byDepth.get(e.depth)!.push(e);
  }

  const center = 150;
  const nodePositions = entries.map((e) => {
    const siblings = byDepth.get(e.depth)!;
    const idx = siblings.indexOf(e);
    const angle = (idx / siblings.length) * 2 * Math.PI - Math.PI / 2;
    const radius = 55 + e.depth * 55;
    return {
      entry: e,
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
      color: DEPTH_COLORS[(e.depth - 1) % DEPTH_COLORS.length],
    };
  });

  return (
    <div className="w-full max-w-2xl">
      <form onSubmit={run} className="glass mb-4 flex items-center gap-2 rounded-2xl p-2">
        <GitBranch className="ml-2 shrink-0 text-zinc-500" size={18} />
        <input
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="e.g. app/processing/chunker.py"
          disabled={loading}
          className="w-full bg-transparent px-1 py-2 text-sm text-white outline-none placeholder:text-zinc-600"
        />
        <button
          type="submit"
          disabled={loading || !filePath.trim()}
          className="flex shrink-0 items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2.5 text-xs font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          Analyze
        </button>
      </form>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-4 flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300"
        >
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          {error}
        </motion.div>
      )}

      {rootFile && (
        <div className="glass rounded-2xl p-5">
          <div className="mb-1 text-xs text-zinc-500">If you change</div>
          <div className="mb-4 font-mono text-sm text-white">{rootFile}</div>

          {entries.length === 0 ? (
            <p className="text-sm text-zinc-500">No other files in this repo import it directly or transitively. Safe to change in isolation (as far as static imports go).</p>
          ) : (
            <>
              <svg viewBox="0 0 300 300" className="mx-auto h-64 w-64">
                {nodePositions.map((p, i) => (
                  <line key={`l${i}`} x1={center} y1={center} x2={p.x} y2={p.y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
                ))}
                <circle cx={center} cy={center} r={14} fill="#fff" />
                <circle cx={center} cy={center} r={14} fill="none" stroke="#6366f1" strokeWidth={2} />
                {nodePositions.map((p, i) => (
                  <g key={i} onClick={() => setSelected(p.entry)} className="cursor-pointer">
                    <circle cx={p.x} cy={p.y} r={9} fill={p.color} opacity={selected === p.entry ? 1 : 0.8} />
                    <circle cx={p.x} cy={p.y} r={9} fill="none" stroke="#0a0a0f" strokeWidth={2} />
                  </g>
                ))}
              </svg>

              <div className="mt-2 flex justify-center gap-4 text-[11px] text-zinc-500">
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: DEPTH_COLORS[0] }} />Direct import</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: DEPTH_COLORS[1] }} />2 hops away</span>
              </div>

              <div className="mt-4 max-h-64 space-y-1.5 overflow-y-auto">
                {entries.map((e, i) => (
                  <button
                    key={i}
                    onClick={() => setSelected(selected === e ? null : e)}
                    className="flex w-full items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-xs transition hover:bg-white/10"
                  >
                    <span className="truncate font-mono text-zinc-300">{e.file}</span>
                    <span className="ml-2 flex shrink-0 items-center gap-1 text-zinc-500">
                      {e.depth} hop{e.depth > 1 ? "s" : ""}
                      <ChevronRight size={12} className={`transition ${selected === e ? "rotate-90" : ""}`} />
                    </span>
                  </button>
                ))}
              </div>

              <AnimatePresence>
                {selected && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 overflow-hidden rounded-lg border border-indigo-400/20 bg-indigo-500/5 p-3"
                  >
                    <div className="mb-1 text-[11px] font-medium text-indigo-300">Import chain (evidence)</div>
                    {selected.evidence.map((line, i) => (
                      <div key={i} className="truncate font-mono text-[11px] text-zinc-400">{line}</div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      )}

      {!rootFile && !loading && !error && (
        <p className="px-1 text-xs text-zinc-600">
          Enter a file path exactly as it appears in the repo (shown in citation chips in Chat) to see what would break if it changed.
        </p>
      )}
    </div>
  );
}

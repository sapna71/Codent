"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Copy, Check, ExternalLink, FileCode2 } from "lucide-react";
import type { CodeResult } from "@/lib/api";

export default function CodeViewer({ result, onClose }: { result: CodeResult | null; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!result) return;
    await navigator.clipboard.writeText(result.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const lines = result?.code.split("\n") ?? [];

  return (
    <AnimatePresence>
      {result && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 260 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-xl flex-col border-l border-white/10 bg-[#0c0c13] shadow-2xl"
          >
            <div className="flex items-start justify-between gap-3 border-b border-white/10 px-5 py-4">
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                  <FileCode2 size={13} />
                  <span className="truncate font-mono">{result.file}</span>
                </div>
                <div className="mt-1 text-sm font-medium text-white">
                  {result.kind === "overview" ? "Repository overview" : result.name}
                  {result.kind !== "overview" && (
                    <span className="ml-2 font-mono text-xs font-normal text-zinc-500">
                      L{result.start_line}–{result.end_line}
                    </span>
                  )}
                </div>
              </div>
              <button onClick={onClose} className="shrink-0 rounded-lg p-1.5 text-zinc-500 transition hover:bg-white/5 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="flex items-center gap-2 border-b border-white/5 px-5 py-2.5">
              <button
                onClick={copy}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-zinc-300 transition hover:bg-white/10"
              >
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                {copied ? "Copied" : "Copy code"}
              </button>
              <a
                href={result.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-zinc-300 transition hover:bg-white/10"
              >
                <ExternalLink size={13} />
                Open on GitHub
              </a>
            </div>

            <div className="flex-1 overflow-auto">
              <pre className="min-w-full px-5 py-4 font-mono text-[12.5px] leading-relaxed text-zinc-300">
                <code>
                  {lines.map((line, i) => (
                    <div key={i} className="flex hover:bg-white/[0.03]">
                      <span className="mr-4 w-10 shrink-0 select-none text-right text-zinc-600">
                        {result.kind === "overview" ? "" : result.start_line + i}
                      </span>
                      <span className="whitespace-pre-wrap break-all">{line || " "}</span>
                    </div>
                  ))}
                </code>
              </pre>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

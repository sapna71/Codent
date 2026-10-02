"use client";

import { AnimatePresence, motion } from "framer-motion";
import { X, Github, Search, GitBranch, MessageSquareCode } from "lucide-react";
import Logo from "./Logo";

const PIPELINE = [
  { icon: Github, label: "Ingest", desc: "Fetch a repo's files via the GitHub API" },
  { icon: Search, label: "Retrieve", desc: "Chunk, embed, and semantically search the code" },
  { icon: MessageSquareCode, label: "Explain", desc: "An LLM answers, grounded only in retrieved code" },
  { icon: GitBranch, label: "Trace", desc: "Every claim links back to a real file and line range" },
];

export default function AboutModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 10 }}
            transition={{ type: "spring", duration: 0.35, bounce: 0.2 }}
            className="fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-white/10 bg-[#0e0e16] p-6 shadow-2xl"
          >
            <button
              onClick={onClose}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-zinc-500 transition hover:bg-white/5 hover:text-white"
            >
              <X size={18} />
            </button>

            <Logo size="lg" />

            <p className="mt-4 text-sm leading-relaxed text-zinc-400">
              Codent points at any GitHub repository and answers plain-English questions about it —
              grounded in the actual code, with every claim traceable to a specific file and line range.
              It isn&apos;t a linter or a security scanner; it&apos;s built for <span className="text-zinc-200">understanding</span>{" "}
              an unfamiliar codebase.
            </p>

            <div className="mt-5 grid grid-cols-2 gap-2.5">
              {PIPELINE.map(({ icon: Icon, label, desc }) => (
                <div key={label} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                  <Icon size={15} className="mb-1.5 text-indigo-400" />
                  <div className="text-xs font-medium text-zinc-200">{label}</div>
                  <div className="mt-0.5 text-[11px] leading-snug text-zinc-500">{desc}</div>
                </div>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap gap-1.5">
              {["FastAPI", "FAISS", "Gemini Embeddings", "Groq LLM", "Next.js"].map((t) => (
                <span key={t} className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-zinc-400">
                  {t}
                </span>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

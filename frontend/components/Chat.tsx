"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, Loader2, Sparkles } from "lucide-react";
import { askQuestion, queryCode, ApiError, type IngestResult, type Source, type CodeResult } from "@/lib/api";
import Message, { type ChatMessage } from "./Message";
import CodeViewer from "./CodeViewer";

const SUGGESTIONS = ["Explain this repository", "Where is the main entry point?", "What are the core modules?"];

export default function Chat({ repo }: { repo: IngestResult }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [codeByKey, setCodeByKey] = useState<Record<string, CodeResult>>({});
  const [viewing, setViewing] = useState<CodeResult | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function keyFor(s: { file: string; start_line: number; end_line: number }) {
    return `${s.file}:${s.start_line}-${s.end_line}`;
  }

  async function send(question: string) {
    if (!question.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const [askRes, queryRes] = await Promise.all([
        askQuestion(repo.repo_key, question),
        queryCode(repo.repo_key, question).catch(() => null),
      ]);

      if (queryRes) {
        setCodeByKey((prev) => {
          const next = { ...prev };
          for (const r of queryRes.results) next[keyFor(r)] = r;
          return next;
        });
      }

      setMessages((m) => [...m, { role: "assistant", text: askRes.answer, sources: askRes.sources }]);
    } catch (err) {
      const text = err instanceof ApiError ? err.message : "Could not reach the backend.";
      setMessages((m) => [...m, { role: "assistant", text }]);
    } finally {
      setLoading(false);
    }
  }

  function handleViewCode(source: Source) {
    const code = codeByKey[keyFor(source)];
    if (code) {
      setViewing(code);
    } else {
      setViewing({ ...source, code: 'Full code preview isn\u2019t available for this source. Use "Open on GitHub" instead.' });
    }
  }

  return (
    <div className="flex h-[calc(100vh-140px)] w-full max-w-2xl flex-col">
      <div className="mb-4 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-2.5">
        <span className="text-sm text-zinc-300">{repo.owner}/{repo.name}</span>
        <span className="text-xs text-zinc-500">{repo.chunk_count} chunks indexed</span>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <Sparkles className="text-indigo-400" size={28} />
            <p className="text-sm text-zinc-500">Ask anything about this codebase.</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-400 transition hover:border-indigo-400/40 hover:text-indigo-300">
                  {s}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {messages.map((m, i) => (
          <Message key={i} message={m} onViewCode={handleViewCode} />
        ))}

        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 pl-11 text-xs text-zinc-500">
            <Loader2 size={13} className="animate-spin" />
            Searching the codebase…
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="glass mt-4 flex items-center gap-2 rounded-2xl p-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="How does checkout work?"
          disabled={loading}
          className="w-full bg-transparent px-3 py-2 text-sm text-white outline-none placeholder:text-zinc-600"
        />
        <button type="submit" disabled={loading || !input.trim()} className="flex shrink-0 items-center justify-center rounded-xl bg-indigo-600 p-2.5 text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40">
          <Send size={16} />
        </button>
      </form>

      <CodeViewer result={viewing} onClose={() => setViewing(null)} />
    </div>
  );
}

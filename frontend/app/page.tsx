"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Github, Loader2, AlertCircle, ArrowRight, Sparkles, MessageSquare, GitBranch, BarChart3 } from "lucide-react";
import { ingestRepo, ApiError, type IngestResult } from "@/lib/api";
import { isValidGithubUrl } from "@/lib/github";
import Chat from "@/components/Chat";
import Header from "@/components/Header";
import Tabs from "@/components/Tabs";
import ImpactExplorer from "@/components/ImpactExplorer";
import StatsPanel from "@/components/StatsPanel";

const TABS = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "impact", label: "Impact", icon: GitBranch },
  { id: "stats", label: "Stats", icon: BarChart3 },
];

type Status = "idle" | "loading" | "success" | "error";

export default function Home() {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string>("");
  const [activeTab, setActiveTab] = useState("chat");

  const urlLooksValid = url.length === 0 || isValidGithubUrl(url);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValidGithubUrl(url)) {
      setStatus("error");
      setError("That doesn't look like a valid GitHub repository URL.");
      return;
    }

    setStatus("loading");
    setError("");
    try {
      const data = await ingestRepo(url);
      setResult(data);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : "Could not reach the backend.");
    }
  }

  if (status === "success" && result) {
    return (
      <>
        <Header />
        <main className="relative flex min-h-screen flex-col items-center px-6 pb-10 pt-20">
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-0 h-[400px] w-[600px] -translate-x-1/2 rounded-full bg-indigo-600/10 blur-[120px]" />
          </div>
          <div className="w-full max-w-2xl">
            <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
          </div>
          {activeTab === "chat" && <Chat repo={result} />}
          {activeTab === "impact" && <ImpactExplorer repo={result} />}
          {activeTab === "stats" && <StatsPanel repo={result} />}
        </main>
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-1/3 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-indigo-600/20 blur-[120px]" />
          <div className="absolute right-1/4 top-2/3 h-[300px] w-[300px] rounded-full bg-emerald-500/10 blur-[100px]" />
        </div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full max-w-xl">
          <div className="mb-10 text-center">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-zinc-400"
            >
              <Sparkles size={14} className="text-indigo-400" />
              AI-powered codebase understanding
            </motion.div>
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">Codent</h1>
            <p className="mt-3 text-zinc-400">Point it at a repository. Ask it anything.</p>
          </div>

          <form onSubmit={handleSubmit} className="glass rounded-2xl p-2 shadow-2xl">
            <div className="flex items-center gap-2 p-2">
              <Github className="ml-2 shrink-0 text-zinc-500" size={20} />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                disabled={status === "loading"}
                className={`w-full bg-transparent py-2 text-sm text-white outline-none placeholder:text-zinc-600 ${!urlLooksValid ? "text-red-400" : ""}`}
              />
              <button
                type="submit"
                disabled={status === "loading" || url.length === 0}
                className="flex shrink-0 items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {status === "loading" ? <Loader2 size={16} className="animate-spin" /> : (<>Index <ArrowRight size={14} /></>)}
              </button>
            </div>
          </form>

          <AnimatePresence mode="wait">
            {status === "loading" && (
              <motion.div
                key="loading"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 flex items-center gap-2 px-2 text-sm text-zinc-400"
              >
                <Loader2 size={14} className="animate-spin text-indigo-400" />
                Fetching, filtering, chunking, and embedding the repository…
              </motion.div>
            )}

            {status === "error" && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-4 flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300"
              >
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                {error}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </main>
    </>
  );
}

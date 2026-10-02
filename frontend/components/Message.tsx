"use client";

import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import type { Source } from "@/lib/api";
import CitationChip from "./CitationChip";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
}

function renderAnswerWithRefs(text: string, sources: Source[]) {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (!match) return <span key={i}>{part}</span>;
    const ref = Number(match[1]);
    const exists = sources.some((s) => s.ref === ref);
    return exists ? (
      <a key={i} href={`#source-${ref}`} className="mx-0.5 rounded bg-indigo-500/20 px-1 font-mono text-indigo-300 hover:bg-indigo-500/30">
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    );
  });
}

export default function Message({ message, onViewCode }: { message: ChatMessage; onViewCode?: (source: Source) => void }) {
  const isUser = message.role === "user";

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${isUser ? "bg-indigo-600" : "bg-white/10"}`}>
        {isUser ? <User size={15} className="text-white" /> : <Bot size={15} className="text-indigo-300" />}
      </div>

      <div className={`max-w-[85%] ${isUser ? "text-right" : ""}`}>
        <div className={`glass inline-block rounded-2xl px-4 py-3 text-sm leading-relaxed ${isUser ? "bg-indigo-600/20" : ""}`}>
          {message.sources ? renderAnswerWithRefs(message.text, message.sources) : message.text}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.sources.map((s) => (
              <span key={s.ref} id={`source-${s.ref}`}>
                <CitationChip source={s} onView={onViewCode} />
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

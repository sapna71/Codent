"use client";

import { motion } from "framer-motion";

export interface TabDef {
  id: string;
  label: string;
  icon: React.ElementType;
}

export default function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="mb-4 flex gap-1 rounded-xl border border-white/10 bg-white/5 p-1">
      {tabs.map((t) => {
        const Icon = t.icon;
        const isActive = t.id === active;
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className="relative flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition"
          >
            {isActive && (
              <motion.div
                layoutId="tab-pill"
                className="absolute inset-0 rounded-lg bg-indigo-600"
                transition={{ type: "spring", duration: 0.4, bounce: 0.2 }}
              />
            )}
            <span className={`relative z-10 flex items-center gap-1.5 ${isActive ? "text-white" : "text-zinc-400"}`}>
              <Icon size={13} />
              {t.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

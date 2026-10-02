"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { FileStack, Filter, Boxes } from "lucide-react";
import type { IngestResult } from "@/lib/api";

const COLORS = ["#6366f1", "#27272a"];

export default function StatsPanel({ repo }: { repo: IngestResult }) {
  const discarded = Math.max(repo.raw_file_count - repo.filtered_file_count, 0);
  const avgChunksPerFile = repo.filtered_file_count > 0 ? (repo.chunk_count / repo.filtered_file_count).toFixed(1) : "0";

  const barData = [
    { name: "Raw files", value: repo.raw_file_count },
    { name: "Source files", value: repo.filtered_file_count },
    { name: "Chunks", value: repo.chunk_count },
  ];

  const pieData = [
    { name: "Kept as source", value: repo.filtered_file_count },
    { name: "Filtered out", value: discarded },
  ];

  return (
    <div className="w-full max-w-2xl space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <StatCard icon={FileStack} label="Files scanned" value={repo.raw_file_count} />
        <StatCard icon={Filter} label="Source files kept" value={repo.filtered_file_count} />
        <StatCard icon={Boxes} label="Chunks indexed" value={repo.chunk_count} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-5"
      >
        <h3 className="mb-3 text-sm font-medium text-zinc-300">Pipeline volume</h3>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 16 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={90}
              tick={{ fill: "#a1a1aa", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ background: "#16161f", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#e4e4e7" }}
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
            />
            <Bar dataKey="value" fill="#6366f1" radius={[0, 6, 6, 0]} barSize={22} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass flex flex-col items-center rounded-2xl p-5"
        >
          <h3 className="mb-2 self-start text-sm font-medium text-zinc-300">Filtering ratio</h3>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={pieData} dataKey="value" innerRadius={38} outerRadius={55} paddingAngle={3}>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#16161f", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-1 flex gap-3 text-[11px] text-zinc-500">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-indigo-500" />Kept</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-zinc-700" />Filtered</span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass flex flex-col justify-center rounded-2xl p-5"
        >
          <div className="text-xs text-zinc-500">Avg. chunks per file</div>
          <div className="mt-1 text-3xl font-semibold text-white">{avgChunksPerFile}</div>
          <div className="mt-2 text-xs text-zinc-500">
            Higher usually means larger files with many functions/classes.
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-xl p-3.5">
      <Icon size={15} className="mb-2 text-indigo-400" />
      <div className="text-lg font-semibold text-white">{value.toLocaleString()}</div>
      <div className="mt-0.5 text-[11px] text-zinc-500">{label}</div>
    </motion.div>
  );
}

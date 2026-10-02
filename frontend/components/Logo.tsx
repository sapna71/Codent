import { Braces } from "lucide-react";

export default function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const box = size === "lg" ? "h-11 w-11" : size === "sm" ? "h-7 w-7" : "h-9 w-9";
  const icon = size === "lg" ? 20 : size === "sm" ? 14 : 17;
  const text = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";

  return (
    <div className="flex items-center gap-2.5">
      <div className={`flex ${box} shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-600/20`}>
        <Braces size={icon} className="text-white" strokeWidth={2.3} />
      </div>
      <span className={`${text} font-semibold tracking-tight text-white`}>Codent</span>
    </div>
  );
}

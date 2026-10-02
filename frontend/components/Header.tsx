"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import Logo from "./Logo";
import AboutModal from "./AboutModal";

export default function Header() {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <>
      <header className="fixed left-0 right-0 top-0 z-30 flex items-center justify-between border-b border-white/5 bg-[#0a0a0f]/70 px-6 py-3.5 backdrop-blur-md">
        <Logo size="sm" />
        <button
          onClick={() => setAboutOpen(true)}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-zinc-400 transition hover:bg-white/5 hover:text-white"
        >
          <Info size={13} />
          About
        </button>
      </header>
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </>
  );
}

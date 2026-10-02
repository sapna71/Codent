import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codent — Understand any codebase",
  description: "Ask questions about any GitHub repository and get grounded, cited answers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}

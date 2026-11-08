import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { ExpertAuthorityNote, SyntheticBanner } from "@/components/notices";
import { getManifest } from "@/lib/data";

import "./globals.css";

export const metadata: Metadata = {
  title: "Materia Incerta",
  description:
    "How confident can we be about which plant a Byzantine drug name refers to, and which compounds depend on that answer?",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const manifest = getManifest();
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        {manifest.synthetic ? <SyntheticBanner /> : null}
        <header className="border-b bg-card">
          <div className="mx-auto flex max-w-6xl flex-wrap items-baseline justify-between gap-2 px-4 py-3">
            <Link href="/" className="font-serif text-xl font-semibold tracking-tight">
              Materia Incerta
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/" className="hover:underline">
                Names
              </Link>
              <Link href="/benchmark/" className="hover:underline">
                Benchmark and limits
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        <footer className="border-t">
          <div className="mx-auto max-w-6xl space-y-1 px-4 py-4">
            <ExpertAuthorityNote />
            <p className="text-xs text-muted-foreground">
              Built on Lardos et al. (2024), WCVP and LOTUS. Sources and licences are listed on the{" "}
              <Link href="/benchmark/#sources" className="underline">
                benchmark and limits
              </Link>{" "}
              page. Pipeline v{manifest.pipeline_version}.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

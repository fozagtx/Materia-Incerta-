"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { StabilityBadgeView } from "@/components/labels";
import { Badge } from "@/components/ui/badge";
import { Table, Td, Th } from "@/components/ui/table";
import type { IndexRow } from "@/lib/types";

function fold(s: string): string {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

export function NameSearch({ names }: { names: IndexRow[] }) {
  const [query, setQuery] = useState("");
  const rows = useMemo(() => {
    const q = fold(query.trim());
    if (!q) return names;
    return names.filter((n) => [n.greek_name, n.transliteration, n.lemma_tag].some((f) => fold(f).includes(q)));
  }, [names, query]);

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="sr-only">Search names</span>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Greek name or transliteration"
          className="w-full rounded-md border bg-card px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent/40 sm:max-w-md"
        />
      </label>
      <Table>
        <thead>
          <tr>
            <Th>Greek name</Th>
            <Th>Transliteration</Th>
            <Th className="text-right">Candidates</Th>
            <Th>Stability</Th>
            <Th />
          </tr>
        </thead>
        <tbody>
          {rows.map((n) => (
            <tr key={n.lemma_tag} className="hover:bg-muted/60">
              <Td className="font-serif text-base">
                <Link href={`/names/${n.lemma_tag}/`} className="hover:underline">
                  {n.greek_name}
                </Link>
              </Td>
              <Td className="italic">{n.transliteration}</Td>
              <Td className="text-right tabular-nums">{n.candidate_count}</Td>
              <Td>
                <StabilityBadgeView badge={n.stability} />
              </Td>
              <Td className="space-x-1 text-right">
                {n.hazard ? <Badge variant="danger">hazardous candidate</Badge> : null}
                {!n.has_model_scores ? <Badge variant="outline">expert scores only</Badge> : null}
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
      {rows.length === 0 ? <p className="text-sm text-muted-foreground">No names match “{query}”.</p> : null}
    </div>
  );
}

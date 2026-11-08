import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CandidateTable } from "@/components/candidate-table";
import { CompoundLedger } from "@/components/compound-ledger";
import { EvidenceMatrix } from "@/components/evidence-matrix";
import { HazardLabel } from "@/components/labels";
import {
  CandidatePoolNotice,
  ExpertAuthorityNote,
  FirstRankFootnote,
  TextWithheldNote,
} from "@/components/notices";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getCase, getIndex } from "@/lib/data";

// Placeholder param used only when no names have been exported, because a
// static export needs at least one path for a dynamic route.
const EMPTY = "_none";

export const dynamicParams = false;

export function generateStaticParams(): { lemma: string }[] {
  const names = getIndex();
  if (names.length === 0) return [{ lemma: EMPTY }];
  return names.map((n) => ({ lemma: n.lemma_tag }));
}

type Props = { params: Promise<{ lemma: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { lemma } = await params;
  const c = getCase(lemma);
  return { title: c ? `${c.transliteration} · Materia Incerta` : "Materia Incerta" };
}

export default async function PlantCasePage({ params }: Props) {
  const { lemma } = await params;
  const data = getCase(lemma);
  if (!data) {
    if (lemma === EMPTY) {
      return <p className="text-sm text-muted-foreground">No names have been exported yet.</p>;
    }
    notFound();
  }
  const allCandidates = data.dmm_plants.flatMap((p) => p.candidates);
  const hazards = Array.from(new Set(allCandidates.map((c) => c.hazard).filter((h): h is string => Boolean(h))));

  return (
    <article className="space-y-6">
      <div className="text-sm">
        <Link href="/" className="text-muted-foreground hover:underline">
          ← All names
        </Link>
      </div>
      <header className="space-y-2">
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="font-serif text-4xl font-semibold">{data.greek_name}</h1>
          <span className="text-xl italic text-muted-foreground">{data.transliteration}</span>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <Badge variant="outline">lemma {data.lemma_tag}</Badge>
          {data.dmm_plants.map((p) => (
            <Badge key={p.dmm_id} variant="outline">
              Dioscorides {p.chapter ?? p.dmm_id}
            </Badge>
          ))}
          {data.partition ? (
            <Badge variant="accent">{data.partition === "tuning" ? "tuning name" : "held-out name"}</Badge>
          ) : null}
        </div>
        {hazards.map((h) => (
          <HazardLabel key={h} text={h} />
        ))}
        <CandidatePoolNotice />
        <ExpertAuthorityNote />
        {data.text_withheld ? <TextWithheldNote /> : null}
      </header>

      {data.dmm_plants.map((plant) => (
        <section key={plant.dmm_id} className="space-y-4">
          <h2 className="font-serif text-2xl font-semibold">
            Dioscorides {plant.chapter ?? plant.dmm_id}
            {plant.plant_type ? <span className="ml-2 text-base font-normal text-muted-foreground">{plant.plant_type}</span> : null}
          </h2>

          <Card>
            <CardTitle>Ranked candidates</CardTitle>
            <CardDescription>
              Degree of congruence is feature categories that match minus categories that conflict. Strong at 5 or
              above, Moderate at 3 to 4, Weak below 3. Botanical evidence only.
            </CardDescription>
            <div className="mt-3">
              <CandidateTable candidates={plant.candidates} />
            </div>
            <div className="mt-3">
              <FirstRankFootnote />
            </div>
          </Card>

          <Card>
            <CardTitle>Evidence matrix</CardTitle>
            <CardDescription>
              Each ancient detail against each candidate&apos;s modern flora description. Model scoring saw the texts with
              all plant names removed. A model match needs a supporting quote from both texts, or it counts as absent.
            </CardDescription>
            <div className="mt-3">
              <EvidenceMatrix details={plant.details} candidates={plant.candidates} evidence={plant.evidence} />
            </div>
          </Card>
        </section>
      ))}

      <section className="space-y-3">
        <h2 className="font-serif text-2xl font-semibold">Compound ledger</h2>
        <Card>
          <CompoundLedger ledger={data.ledger} candidates={allCandidates} />
        </Card>
      </section>
    </article>
  );
}

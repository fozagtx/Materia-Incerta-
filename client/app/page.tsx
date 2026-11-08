import { NameSearch } from "@/components/name-search";
import { CandidatePoolNotice } from "@/components/notices";
import { getIndex, getManifest } from "@/lib/data";

export default function NameIndex() {
  const names = getIndex();
  const manifest = getManifest();
  return (
    <div className="space-y-6">
      <section className="max-w-3xl space-y-2">
        <h1 className="font-serif text-3xl font-semibold tracking-tight">Which plant is meant?</h1>
        <p className="text-muted-foreground">
          Plant names from John the Physician&apos;s <em>Therapeutics</em>, linked to Dioscorides&apos;{" "}
          <em>De materia medica</em>. Each name shows the candidate species suggested in the literature, how well
          each fits the ancient description, how stable that ranking is, and which compounds depend on the answer.
        </p>
        <CandidatePoolNotice />
      </section>
      {names.length === 0 ? (
        <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">No results exported yet.</p>
          <p className="mt-1">
            The pipeline has not been run on the Lardos data. Run <code>python -m materia_incerta run --all</code>,
            or <code>python -m materia_incerta demo</code> for synthetic data while building the site.
          </p>
        </div>
      ) : (
        <NameSearch names={names} />
      )}
      <p className="text-xs text-muted-foreground">
        Stability badges use the expert scores, resampled {manifest.constants.n_resamples.toLocaleString("en")} times
        over feature categories.
      </p>
    </div>
  );
}

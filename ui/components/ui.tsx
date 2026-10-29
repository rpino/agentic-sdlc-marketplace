import type { Feature, State } from "@/lib/sdlc";

const STATUS_STYLE: Record<string, string> = {
  approved: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  in_review: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300",
  draft: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  reopened: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  needs_revalidation: "bg-orange-100 text-orange-900 dark:bg-orange-950 dark:text-orange-300",
  not_started: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

export const words = (s: string) => s.replace(/_/g, " ");

export function StatusChip({ status }: { status: string }) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.not_started;
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>{words(status)}</span>;
}

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">{title}</h2>
      {children}
    </section>
  );
}

export function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">{children}</div>;
}

/** The phase the feature is working on: the first phase of its lane that is not approved yet. */
export function currentPhase(feature: Feature): string | null {
  return feature.lane.find((p) => feature.phases[p]?.status !== "approved") ?? null;
}

export type Waiting = { feature: Feature; phase: string };

/** Every phase across a project's features that is waiting for a human to approve it. */
export function waitingForApproval(state: State): Waiting[] {
  return Object.values(state.features).flatMap((feature) =>
    feature.lane.filter((p) => feature.phases[p]?.status === "in_review").map((phase) => ({ feature, phase })),
  );
}

export function openIssueCount(state: State): number {
  return Object.values(state.features).reduce(
    (n, f) => n + f.lane.reduce((m, p) => m + (f.phases[p]?.open_issues ?? []).filter((i) => !i.resolved).length, 0),
    0,
  );
}

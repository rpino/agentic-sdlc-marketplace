import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, Section, StatusChip, currentPhase, words } from "@/components/ui";
import { getProject } from "@/lib/registry";
import { describeError, readNext, readState, readTrace, readVerify } from "@/lib/sdlc";

export const dynamic = "force-dynamic";

export default async function ProjectPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ feature?: string }>;
}) {
  const { id } = await params;
  const { feature: requested } = await searchParams;
  const project = getProject(id);
  if (!project) notFound();

  let state;
  try {
    state = await readState(project.path);
  } catch (e) {
    return (
      <div>
        <h1 className="text-2xl font-semibold">{project.path}</h1>
        <p className="mt-4 text-sm text-red-600">Could not read this project: {describeError(e)}</p>
      </div>
    );
  }

  const slug = requested && state.features[requested] ? requested : state.active_feature;
  const feature = state.features[slug];
  const [next, trace, verify] = await Promise.all([
    readNext(project.path, slug).catch(() => null),
    readTrace(project.path, slug).catch(() => null),
    readVerify(project.path, slug).catch(() => null),
  ]);
  const current = currentPhase(feature);
  const issues = feature.lane.flatMap((p) =>
    (feature.phases[p].open_issues ?? []).filter((i) => !i.resolved).map((i) => ({ ...i, phase: p })),
  );
  const staleEntries = Object.entries(verify?.stale ?? {});
  const history = state.history.filter((h) => !h.feature || h.feature === slug).slice(-12).reverse();

  return (
    <div>
      <p className="text-sm text-zinc-500">
        <Link href="/">Projects</Link> / {project.path}
      </p>
      <h1 className="mt-1 text-2xl font-semibold">{state.project}</h1>

      <div className="mt-3 flex flex-wrap gap-2">
        {Object.values(state.features).map((f) => (
          <Link
            key={f.slug}
            href={`/projects/${id}?feature=${f.slug}`}
            className={`rounded-full border px-3 py-1 text-sm no-underline hover:no-underline ${
              f.slug === slug
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-300 dark:border-zinc-700"
            }`}
          >
            {f.name} <span className="opacity-60">({f.type})</span>
          </Link>
        ))}
      </div>

      <Section title="Pipeline">
        <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          {feature.lane.map((p) => {
            const ph = feature.phases[p];
            return (
              <li key={p}>
                <div
                  className={`h-full rounded-lg border p-3 ${
                    p === current ? "border-zinc-900 dark:border-zinc-100" : "border-zinc-200 dark:border-zinc-800"
                  } bg-white dark:bg-zinc-900`}
                >
                  <div className="text-sm font-medium capitalize">{words(p)}</div>
                  <div className="mt-1">
                    <StatusChip status={ph.status} />
                  </div>
                  {ph.approved_by && (
                    <div className="mt-1 text-xs text-zinc-500">
                      by {ph.approved_by}, {ph.approved_on}
                    </div>
                  )}
                  {(verify?.stale?.[p]?.length ?? 0) > 0 && <div className="mt-1 text-xs text-orange-600">approval is stale</div>}
                </div>
              </li>
            );
          })}
        </ol>
      </Section>

      <Section title="What is next">
        <Card>
          {next && next.phase ? (
            <div className="space-y-1 text-sm">
              <div>
                <span className="font-medium capitalize">{words(next.phase)}</span> <StatusChip status={next.status ?? "not_started"} />
              </div>
              <div className="text-zinc-600 dark:text-zinc-400">{next.action}</div>
              <div>
                <span className="text-zinc-500">Gate:</span> {next.gate} · <span className="text-zinc-500">Approver:</span> {next.approver}
              </div>
              {next.agents && next.agents.length > 0 && (
                <div>
                  <span className="text-zinc-500">Reviewer agents:</span> {next.agents.join(", ")}
                </div>
              )}
              {next.conditional_agents && next.conditional_agents.length > 0 && (
                <div>
                  <span className="text-zinc-500">Conditional:</span> {next.conditional_agents.map((c) => c.agent).join(", ")}
                </div>
              )}
              {next.living_spec && next.living_spec.mode !== "none" && (
                <div>
                  <span className="text-zinc-500">Living spec:</span> {next.living_spec.mode} ·{" "}
                  {next.living_spec.exists ? "exists" : "not created yet"}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-zinc-500">{next?.message ?? "All phases are approved."}</p>
          )}
        </Card>
      </Section>

      <Section title={`Open issues (${issues.length})`}>
        {issues.length === 0 ? (
          <p className="text-sm text-zinc-500">No open decisions.</p>
        ) : (
          <ul className="space-y-2">
            {issues.map((i) => (
              <li key={`${i.phase}-${i.id}`}>
                <Card>
                  <div className="text-sm">
                    <span className="font-mono text-xs text-zinc-500">{i.id}</span> · <span className="capitalize">{words(i.phase)}</span>
                    <div className="mt-1">{i.text}</div>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {staleEntries.length > 0 && (
        <Section title="Approvals that changed since they were given">
          <ul className="space-y-1 text-sm">
            {staleEntries.map(([phase, files]) => (
              <li key={phase}>
                <span className="font-medium capitalize">{words(phase)}</span>: {files.join(", ")}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Traceability">
        {!trace || trace.matrix.length === 0 ? (
          <p className="text-sm text-zinc-500">No acceptance criteria yet.</p>
        ) : (
          <>
            <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-zinc-100 text-xs uppercase text-zinc-500 dark:bg-zinc-900">
                  <tr>
                    <th className="px-3 py-2">AC</th>
                    <th className="px-3 py-2">Story</th>
                    <th className="px-3 py-2">Tasks</th>
                    <th className="px-3 py-2">Test cases</th>
                    <th className="px-3 py-2">Results</th>
                  </tr>
                </thead>
                <tbody>
                  {trace.matrix.map((row) => (
                    <tr key={row.ac} className="border-t border-zinc-200 dark:border-zinc-800">
                      <td className="px-3 py-2 font-mono text-xs">{row.ac}</td>
                      <td className="px-3 py-2">{row.story}</td>
                      <td className="px-3 py-2">{row.tasks.join(", ") || "—"}</td>
                      <td className="px-3 py-2">{row.test_cases.join(", ") || "—"}</td>
                      <td className="px-3 py-2">{Object.values(row.results).join(", ") || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {trace.issues.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-sm text-orange-700 dark:text-orange-400">
                {trace.issues.map((t, n) => (
                  <li key={n}>{t.message}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </Section>

      <Section title="Artifacts">
        <ul className="space-y-1 text-sm">
          {feature.lane.flatMap((p) =>
            feature.phases[p].artifacts
              .filter((a) => a.toLowerCase().endsWith(".md"))
              .map((a) => (
                <li key={`${p}-${a}`}>
                  <span className="capitalize text-zinc-500">{words(p)}:</span>{" "}
                  <Link href={`/projects/${id}/artifact?path=${encodeURIComponent(a)}`}>{a}</Link>
                </li>
              )),
          )}
        </ul>
      </Section>

      <Section title="Recent activity">
        <ul className="space-y-1 text-sm">
          {history.map((h, n) => (
            <li key={n} className="text-zinc-600 dark:text-zinc-400">
              <span className="font-mono text-xs">{h.ts.slice(0, 16).replace("T", " ")}</span> · {words(h.event)}
              {h.phase ? ` · ${h.phase}` : ""}
              {h.note ? ` · ${h.note}` : ""}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

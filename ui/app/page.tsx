import Link from "next/link";
import { Card, Section, StatusChip, currentPhase, openIssueCount, waitingForApproval, words } from "@/components/ui";
import { listProjects } from "@/lib/registry";
import { describeError, readState, type State } from "@/lib/sdlc";
import { addProjectAction, removeProjectAction } from "./actions";

export const dynamic = "force-dynamic";

type Row = { id: string; path: string; state?: State; error?: string };

export default async function Home({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const rows: Row[] = await Promise.all(
    listProjects().map(async (p) => {
      try {
        return { id: p.id, path: p.path, state: await readState(p.path) };
      } catch (e) {
        return { id: p.id, path: p.path, error: describeError(e) };
      }
    }),
  );
  const inbox = rows.flatMap((r) =>
    r.state ? waitingForApproval(r.state).map((w) => ({ ...w, id: r.id, project: r.state!.project })) : [],
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold">Projects</h1>

      <Section title={`Waiting for approval (${inbox.length})`}>
        {inbox.length === 0 ? (
          <p className="text-sm text-zinc-500">Nothing is waiting for a decision.</p>
        ) : (
          <ul className="space-y-2">
            {inbox.map((w) => (
              <li key={`${w.id}-${w.feature.slug}-${w.phase}`}>
                <Card>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <Link href={`/projects/${w.id}?feature=${w.feature.slug}`} className="font-medium">
                        {w.project} · {w.feature.name}
                      </Link>
                      <div className="text-sm text-zinc-500">
                        {w.phase} is in review. Approve it in Claude Code with <code>/sdlc-core:approve {w.phase}</code>.
                      </div>
                    </div>
                    <StatusChip status="in_review" />
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="All projects">
        {rows.length === 0 ? (
          <p className="text-sm text-zinc-500">No projects yet. Add a folder that has a <code>.sdlc</code> directory.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 text-xs uppercase text-zinc-500 dark:bg-zinc-900">
                <tr>
                  <th className="px-3 py-2">Project</th>
                  <th className="px-3 py-2">Active feature</th>
                  <th className="px-3 py-2">Phase</th>
                  <th className="px-3 py-2">Open issues</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const active = r.state?.features[r.state.active_feature];
                  const phase = active ? currentPhase(active) : null;
                  return (
                    <tr key={r.id} className="border-t border-zinc-200 align-top dark:border-zinc-800">
                      <td className="px-3 py-2">
                        <Link href={`/projects/${r.id}`} className="font-medium">
                          {r.state?.project ?? r.path}
                        </Link>
                        <div className="text-xs text-zinc-500">{r.path}</div>
                        {r.error && <div className="mt-1 text-xs text-red-600">Could not read this project: {r.error}</div>}
                      </td>
                      <td className="px-3 py-2">{active ? `${active.name} (${active.type})` : "—"}</td>
                      <td className="px-3 py-2">
                        {active && phase ? (
                          <span className="flex items-center gap-2">
                            {words(phase)} <StatusChip status={active.phases[phase].status} />
                          </span>
                        ) : active ? (
                          "all approved"
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-3 py-2">{r.state ? openIssueCount(r.state) : "—"}</td>
                      <td className="px-3 py-2 text-right">
                        <form action={removeProjectAction}>
                          <input type="hidden" name="id" value={r.id} />
                          <button className="text-xs text-zinc-500 hover:text-red-600">Remove</button>
                        </form>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section title="Add a project">
        <form action={addProjectAction} className="flex flex-wrap gap-2">
          <input
            name="path"
            required
            placeholder="C:\path\to\your\project"
            className="min-w-72 flex-1 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900">
            Add
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </Section>
    </div>
  );
}

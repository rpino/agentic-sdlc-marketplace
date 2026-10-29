import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

export type Issue = { id: string; text: string; raised: string; resolved: boolean; note?: string };
export type Phase = {
  status: "not_started" | "draft" | "in_review" | "approved" | "reopened" | "needs_revalidation";
  artifacts: string[];
  approved_by: string | null;
  approved_on: string | null;
  open_issues: Issue[];
};
export type Feature = {
  name: string;
  slug: string;
  type: string;
  lane: string[];
  docs_root: string;
  phases: Record<string, Phase>;
};
export type HistoryEvent = { ts: string; event: string; feature?: string; phase?: string; by?: string; note?: string };
export type State = {
  root: string;
  project: string;
  next_phase: string | null;
  code_unlocked: boolean;
  approvers: Record<string, string>;
  active_feature: string;
  features: Record<string, Feature>;
  history: HistoryEvent[];
};
export type NextInfo = {
  feature: string;
  type?: string;
  phase: string | null;
  title?: string;
  status?: string;
  skills?: string[];
  agents?: string[];
  conditional_agents?: { agent: string; run_if: string }[];
  living_spec?: { mode: string; path: string; exists: boolean };
  artifacts?: string[];
  gate?: string;
  approver?: string;
  action?: string;
  message?: string;
};
export type Trace = {
  counts: Record<string, number>;
  matrix: { ac: string; story: string; tasks: string[]; test_cases: string[]; results: Record<string, string> }[];
  issues: { check: string; message: string }[];
};
export type Verify = { stale: Record<string, string[]> };

/** The state script that ships in this repository. Override with SDLC_STATE_SCRIPT. */
function scriptPath(): string {
  return process.env.SDLC_STATE_SCRIPT || path.resolve(process.cwd(), "..", "plugins", "sdlc-core", "scripts", "sdlc_state.py");
}

function pythonCommand(): string {
  return process.env.SDLC_PYTHON || (process.platform === "win32" ? "python" : "python3");
}

const SLUG = /^[a-z0-9][a-z0-9-]*$/;

/**
 * Run one read-only subcommand of the state script in a project folder and parse its JSON.
 * Arguments are fixed strings plus a validated feature slug, and no shell is involved.
 */
async function sdlcJson<T>(projectPath: string, args: string[], feature?: string): Promise<T> {
  const full = [scriptPath(), ...args];
  if (feature) {
    if (!SLUG.test(feature)) throw new Error("Invalid feature name.");
    full.push("--feature", feature);
  }
  const { stdout } = await run(pythonCommand(), full, {
    cwd: projectPath,
    timeout: 20_000,
    maxBuffer: 8 * 1024 * 1024,
    windowsHide: true,
  });
  return JSON.parse(stdout) as T;
}

export const readState = (projectPath: string) => sdlcJson<State>(projectPath, ["status", "--json", "--all"]);
export const readNext = (projectPath: string, feature: string) => sdlcJson<NextInfo>(projectPath, ["next", "--json"], feature);
export const readTrace = (projectPath: string, feature: string) => sdlcJson<Trace>(projectPath, ["trace", "--json"], feature);
export const readVerify = (projectPath: string, feature: string) => sdlcJson<Verify>(projectPath, ["verify", "--json"], feature);

export function describeError(e: unknown): string {
  const err = e as { stderr?: string; message?: string };
  const text = (err.stderr || err.message || String(e)).trim();
  return text.split("\n").slice(-3).join(" ").slice(0, 300);
}

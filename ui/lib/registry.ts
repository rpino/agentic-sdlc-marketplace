import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export type Project = { id: string; path: string; addedAt: string };

/** The UI's own list of registered project folders. Process state stays in each project's .sdlc/. */
export function registryFile(): string {
  return process.env.SDLC_UI_DATA || path.join(os.homedir(), ".agentic-sdlc-ui", "projects.json");
}

export function projectId(projectPath: string): string {
  return createHash("sha1").update(projectPath.toLowerCase()).digest("hex").slice(0, 8);
}

export function listProjects(): Project[] {
  try {
    const data = JSON.parse(fs.readFileSync(/* turbopackIgnore: true */ registryFile(), "utf-8"));
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function save(projects: Project[]): void {
  const file = registryFile();
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(projects, null, 2));
}

export function getProject(id: string): Project | undefined {
  return listProjects().find((p) => p.id === id);
}

/** Register a folder. It must already be an Agentic SDLC project (it has .sdlc/state.json). */
export function addProject(input: string): { ok: true; project: Project } | { ok: false; error: string } {
  const trimmed = input.trim().replace(/^"(.*)"$/, "$1");
  if (!trimmed) return { ok: false, error: "Enter a folder path." };
  let resolved: string;
  try {
    resolved = fs.realpathSync(path.resolve(trimmed));
  } catch {
    return { ok: false, error: "That folder does not exist." };
  }
  if (!fs.existsSync(path.join(resolved, ".sdlc", "state.json"))) {
    return { ok: false, error: "No .sdlc/state.json there. Run /sdlc-core:init or /sdlc-core:adopt in that folder first." };
  }
  const projects = listProjects();
  const id = projectId(resolved);
  const existing = projects.find((p) => p.id === id);
  if (existing) return { ok: true, project: existing };
  const project = { id, path: resolved, addedAt: new Date().toISOString() };
  save([...projects, project]);
  return { ok: true, project };
}

export function removeProject(id: string): void {
  save(listProjects().filter((p) => p.id !== id));
}

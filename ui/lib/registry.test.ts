import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, describe, it } from "node:test";
import { addProject, getProject, listProjects, removeProject } from "./registry.ts";

describe("project registry", () => {
  let base: string;
  let sdlcProject: string;
  let plainFolder: string;

  before(() => {
    base = fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-ui-reg-"));
    process.env.SDLC_UI_DATA = path.join(base, "data", "projects.json");
    sdlcProject = path.join(base, "app");
    plainFolder = path.join(base, "plain");
    fs.mkdirSync(path.join(sdlcProject, ".sdlc"), { recursive: true });
    fs.writeFileSync(path.join(sdlcProject, ".sdlc", "state.json"), "{}");
    fs.mkdirSync(plainFolder);
  });

  after(() => fs.rmSync(base, { recursive: true, force: true }));

  it("starts empty", () => {
    assert.deepEqual(listProjects(), []);
  });

  it("refuses folders that are not SDLC projects or do not exist", () => {
    const plain = addProject(plainFolder);
    assert.equal(plain.ok, false);
    const missing = addProject(path.join(base, "nope"));
    assert.equal(missing.ok, false);
    assert.equal(addProject("   ").ok, false);
    assert.deepEqual(listProjects(), []);
  });

  it("registers a project once, even if quoted or added again", () => {
    const first = addProject(`"${sdlcProject}"`);
    assert.ok(first.ok);
    const again = addProject(sdlcProject);
    assert.ok(again.ok);
    assert.equal(listProjects().length, 1);
    if (first.ok) assert.deepEqual(getProject(first.project.id)?.path, first.project.path);
  });

  it("removes a project", () => {
    const [p] = listProjects();
    removeProject(p.id);
    assert.deepEqual(listProjects(), []);
  });
});

import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, describe, it } from "node:test";
import { resolveMarkdownInside } from "./safe-path.ts";

describe("resolveMarkdownInside", () => {
  let root: string;
  let outside: string;

  before(() => {
    const base = fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-ui-path-"));
    root = path.join(base, "project");
    outside = path.join(base, "secret.md");
    fs.mkdirSync(path.join(root, "docs"), { recursive: true });
    fs.mkdirSync(path.join(root, ".sdlc"), { recursive: true });
    fs.writeFileSync(path.join(root, "docs", "a.md"), "# a");
    fs.writeFileSync(path.join(root, "docs", "data.json"), "{}");
    fs.writeFileSync(path.join(root, ".sdlc", "notes.md"), "# internal");
    fs.writeFileSync(outside, "# outside");
  });

  after(() => fs.rmSync(path.dirname(root), { recursive: true, force: true }));

  it("accepts a markdown file inside the project", () => {
    const real = resolveMarkdownInside(root, "docs/a.md");
    assert.ok(real && real.endsWith("a.md"));
  });

  it("rejects parent-directory escapes", () => {
    assert.equal(resolveMarkdownInside(root, "../secret.md"), null);
    assert.equal(resolveMarkdownInside(root, "docs/../../secret.md"), null);
  });

  it("rejects absolute paths outside the project", () => {
    assert.equal(resolveMarkdownInside(root, outside), null);
  });

  it("rejects non-markdown files, missing files and directories", () => {
    assert.equal(resolveMarkdownInside(root, "docs/data.json"), null);
    assert.equal(resolveMarkdownInside(root, "docs/missing.md"), null);
    assert.equal(resolveMarkdownInside(root, "docs"), null);
    assert.equal(resolveMarkdownInside(root, ""), null);
  });

  it("rejects the internal .sdlc folder and null bytes", () => {
    assert.equal(resolveMarkdownInside(root, ".sdlc/notes.md"), null);
    assert.equal(resolveMarkdownInside(root, "docs/a.md\0.png"), null);
  });
});

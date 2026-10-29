import fs from "node:fs";
import path from "node:path";

const BLOCKED_TOP_LEVEL = new Set([".sdlc", ".git", "node_modules"]);

/**
 * Resolve a project-relative path to a real file inside `root`, or return null.
 *
 * The artifact viewer shows files from projects the user registered, so it must never leak a file
 * outside the project. A path is accepted only if, after following symlinks, it is inside the
 * project root, is a Markdown file, and is not under .sdlc, .git or node_modules.
 */
export function resolveMarkdownInside(root: string, rel: string): string | null {
  if (!rel || rel.includes("\0") || !/\.md$/i.test(rel)) return null;
  let rootReal: string;
  let real: string;
  try {
    rootReal = fs.realpathSync(root);
    real = fs.realpathSync(path.resolve(rootReal, rel));
  } catch {
    return null;
  }
  const inside = path.relative(rootReal, real);
  if (!inside || inside.startsWith("..") || path.isAbsolute(inside)) return null;
  if (BLOCKED_TOP_LEVEL.has(inside.split(path.sep)[0])) return null;
  try {
    if (!fs.statSync(real).isFile()) return null;
  } catch {
    return null;
  }
  return real;
}

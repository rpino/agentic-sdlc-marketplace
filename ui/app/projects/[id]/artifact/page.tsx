import fs from "node:fs";
import Link from "next/link";
import { notFound } from "next/navigation";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getProject } from "@/lib/registry";
import { resolveMarkdownInside } from "@/lib/safe-path";

export const dynamic = "force-dynamic";

export default async function ArtifactPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ path?: string }>;
}) {
  const { id } = await params;
  const { path: rel = "" } = await searchParams;
  const project = getProject(id);
  if (!project) notFound();
  const file = resolveMarkdownInside(project.path, rel);
  if (!file) notFound();
  const text = fs.readFileSync(file, "utf-8");

  return (
    <div>
      <p className="mb-4 text-sm text-zinc-500">
        <Link href={`/projects/${id}`}>Back to project</Link> / {rel}
      </p>
      <article className="md">
        <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
      </article>
    </div>
  );
}

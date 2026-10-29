"use server";

import { redirect } from "next/navigation";
import { addProject, removeProject } from "@/lib/registry";

/** Register a project folder. This only edits the UI's own list; it never touches a project. */
export async function addProjectAction(formData: FormData) {
  const result = addProject(String(formData.get("path") ?? ""));
  if (!result.ok) redirect(`/?error=${encodeURIComponent(result.error)}`);
  redirect("/");
}

export async function removeProjectAction(formData: FormData) {
  removeProject(String(formData.get("id") ?? ""));
  redirect("/");
}

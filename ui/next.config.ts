import path from "node:path";
import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The app only ever runs locally, so keep response headers conservative.
  poweredByHeader: false,
  // Pin the project root so a stray package-lock.json in a parent folder is never picked up.
  turbopack: { root: path.dirname(fileURLToPath(import.meta.url)) },
};

export default nextConfig;

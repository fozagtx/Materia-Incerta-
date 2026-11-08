import type { NextConfig } from "next";

// Static export only: no server, no API routes, no live model calls.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;

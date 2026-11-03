import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${process.env.API_BASE_URL || "http://127.0.0.1:8000"}/:path*` }];
  },
  /* config options here */
  experimental: {
    // Ingestion can wait for Gemini quota recovery between embedding batches.
    proxyTimeout: 30 * 60 * 1000,
    proxyClientMaxBodySize: "12mb",
    agentFeedback: true,
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

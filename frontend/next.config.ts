import type { NextConfig } from "next";

/** The backend, as this server reaches it. Compose and Render set it; locally
 *  it falls back to the dev server's port. */
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle, so the runtime image does not
  // need node_modules.
  output: "standalone",

  // The browser talks to this origin and never to the backend directly, which
  // is what keeps CORS out of the deployment.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
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

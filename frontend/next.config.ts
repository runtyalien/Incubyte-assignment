import type { NextConfig } from "next";

/* The browser talks to this origin and never to the backend directly, which
 * is what keeps CORS out of the deployment. That used to be a rewrite here;
 * it is now src/app/api/[...path]/route.ts, because a rewrite cannot attach
 * the API key and the browser must not hold one. */

const nextConfig: NextConfig = {
  // Produces a self-contained server bundle, so the runtime image does not
  // need node_modules.
  output: "standalone",

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

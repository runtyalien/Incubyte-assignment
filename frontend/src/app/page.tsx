import { Suspense } from "react";

import { getHealth, type Health } from "@/lib/api";

/**
 * Placeholder landing page.
 *
 * It exists to prove the frontend can reach the backend; the real HR surfaces
 * replace it as they are built.
 */
export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          ACME Salary Management
        </h1>
        <p className="text-sm opacity-70">
          Project scaffold. Employee directory and compensation analytics are
          not built yet.
        </p>
      </header>

      <section
        className="rounded-lg border border-black/10 p-4 text-sm dark:border-white/15"
        aria-live="polite"
      >
        <h2 className="mb-3 font-medium">Backend connection</h2>
        <Suspense fallback={<p className="opacity-60">Checking&hellip;</p>}>
          <BackendStatus />
        </Suspense>
      </section>
    </main>
  );
}

type HealthResult =
  | { ok: true; health: Health }
  | { ok: false; message: string };

/**
 * A failed health check is an expected state here rather than a crash, so it is
 * returned as a value instead of thrown to an error boundary.
 */
async function readHealth(): Promise<HealthResult> {
  try {
    return { ok: true, health: await getHealth() };
  } catch (cause) {
    return {
      ok: false,
      message: cause instanceof Error ? cause.message : "Unknown error",
    };
  }
}

/**
 * Reads the API health endpoint on every request, so it is deliberately kept
 * out of the prerendered shell.
 */
async function BackendStatus() {
  const result = await readHealth();

  if (!result.ok) {
    return (
      <p className="font-mono text-red-600 dark:text-red-400">
        {result.message}
      </p>
    );
  }

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
      <dt className="opacity-60">Status</dt>
      <dd className="font-mono">{result.health.status}</dd>
      <dt className="opacity-60">Service</dt>
      <dd className="font-mono">{result.health.service}</dd>
      <dt className="opacity-60">Environment</dt>
      <dd className="font-mono">{result.health.environment}</dd>
    </dl>
  );
}

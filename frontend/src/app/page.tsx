import { Suspense } from "react";

import { getHealth, type Health } from "@/lib/api";

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

type Checked = { ok: true; health: Health } | { ok: false; reason: string };

// An unreachable API is an expected state on this page, so it comes back as a
// value instead of going to an error boundary.
async function checkBackend(): Promise<Checked> {
  try {
    return { ok: true, health: await getHealth() };
  } catch (err) {
    return { ok: false, reason: err instanceof Error ? err.message : "Unknown error" };
  }
}

// Runs on every request, which is why it sits behind Suspense rather than in
// the prerendered shell.
async function BackendStatus() {
  const checked = await checkBackend();

  if (!checked.ok) {
    return (
      <p className="font-mono text-red-600 dark:text-red-400">
        {checked.reason}
      </p>
    );
  }

  const { status, service, environment } = checked.health;

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
      <dt className="opacity-60">Status</dt>
      <dd className="font-mono">{status}</dd>
      <dt className="opacity-60">Service</dt>
      <dd className="font-mono">{service}</dd>
      <dt className="opacity-60">Environment</dt>
      <dd className="font-mono">{environment}</dd>
    </dl>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, recordPayChange } from "@/lib/api";
import { day, money, position } from "@/lib/format";
import { REASONS, type PayChangeResult, type PayReason } from "@/lib/types";

export function PayChangeForm({
  employeeId,
  currency,
  hiredOn,
  current,
}: {
  employeeId: number;
  currency: string;
  hiredOn: string;
  current: string;
}) {
  const router = useRouter();

  const [effectiveFrom, setEffectiveFrom] = useState(today());
  const [amount, setAmount] = useState("");
  const [why, setWhy] = useState<PayReason>("merit");
  const [note, setNote] = useState("");

  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [done, setDone] = useState<PayChangeResult | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setProblem(null);
    setDone(null);

    try {
      const result = await recordPayChange(employeeId, {
        effective_from: effectiveFrom,
        amount,
        reason: why,
        note: note.trim() || undefined,
      });

      setDone(result);
      setAmount("");
      setNote("");
      // The history and the summary above are server-rendered, so they only
      // move if the server renders them again.
      router.refresh();
    } catch (error) {
      // The API's messages name the employee and the offending value, so they
      // are worth showing as-is rather than replacing with something vaguer.
      setProblem(
        error instanceof ApiError ? error.message : "Could not save that.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3 px-4 py-4">
      <Field label={`New salary (${currency})`}>
        <input
          required
          inputMode="decimal"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder={current || "0.00"}
          className="tnum w-full rounded border border-line bg-background px-2.5 py-1.5 text-sm"
        />
      </Field>

      <Field label="Effective from" hint={`hired ${day(hiredOn)}`}>
        <input
          required
          type="date"
          value={effectiveFrom}
          min={hiredOn}
          onChange={(event) => setEffectiveFrom(event.target.value)}
          className="tnum w-full rounded border border-line bg-background px-2.5 py-1.5 text-sm"
        />
      </Field>

      <Field label="Reason">
        <select
          value={why}
          onChange={(event) => setWhy(event.target.value as PayReason)}
          className="w-full rounded border border-line bg-background px-2 py-1.5 text-sm"
        >
          {REASONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Note" hint="optional">
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={500}
          className="w-full rounded border border-line bg-background px-2.5 py-1.5 text-sm"
        />
      </Field>

      <button
        type="submit"
        disabled={saving || !amount}
        className="w-full rounded bg-accent px-3 py-2 text-sm font-medium text-background disabled:opacity-40"
      >
        {saving ? "Recording…" : "Record change"}
      </button>

      {problem && (
        <p role="alert" className="text-sm text-below">
          {problem}
        </p>
      )}

      {done && <Receipt result={done} />}

      <p className="text-xs text-faint">
        Pay history is append-only. A mistake is fixed by recording a
        correction, not by editing what is already there.
      </p>
    </form>
  );
}

function Receipt({ result }: { result: PayChangeResult }) {
  return (
    <div
      role="status"
      className="rounded border border-line bg-background px-3 py-2 text-sm"
    >
      <p>
        Recorded {money(result.entry.amount)} from{" "}
        {day(result.entry.effective_from)}.
      </p>
      <p className="mt-1 text-xs text-muted">
        {result.in_effect
          ? "This is their pay now."
          : "Filed, but not their current pay — a later record still applies."}
        {result.band_position &&
          ` ${position(result.band_position)} at ${result.compa_ratio}.`}
      </p>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium">{label}</span>
        {hint && <span className="text-xs text-faint">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

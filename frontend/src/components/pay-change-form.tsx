"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  const ids = useId();

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
      <div className="space-y-1.5">
        <Label htmlFor={`${ids}-amount`}>New salary ({currency})</Label>
        <Input
          id={`${ids}-amount`}
          required
          type="number"
          min="0.01"
          step="0.01"
          inputMode="decimal"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder={current || "0.00"}
          className="tnum"
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-baseline justify-between gap-2">
          <Label htmlFor={`${ids}-from`}>Effective from</Label>
          <span className="text-xs text-faint">hired {day(hiredOn)}</span>
        </div>
        <Input
          id={`${ids}-from`}
          required
          type="date"
          value={effectiveFrom}
          min={hiredOn}
          onChange={(event) => setEffectiveFrom(event.target.value)}
          className="tnum"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor={`${ids}-reason`}>Reason</Label>
        <Select
          items={REASONS}
          value={why}
          onValueChange={(value) => setWhy(value as PayReason)}
        >
          <SelectTrigger id={`${ids}-reason`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {REASONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-baseline justify-between gap-2">
          <Label htmlFor={`${ids}-note`}>Note</Label>
          <span className="text-xs text-faint">optional</span>
        </div>
        <Input
          id={`${ids}-note`}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={500}
        />
      </div>

      <Button type="submit" disabled={saving || !amount} className="w-full">
        {saving ? "Recording…" : "Record change"}
      </Button>

      {problem && (
        <p role="alert" className="text-sm text-destructive">
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
      className="rounded-md border bg-background px-3 py-2 text-sm"
    >
      <p>
        Recorded {money(result.entry.amount)} from{" "}
        {day(result.entry.effective_from)}.
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        {result.in_effect
          ? "This is their pay now."
          : "Filed, but not their current pay — a later record still applies."}
        {result.band_position &&
          ` ${position(result.band_position)} at ${result.compa_ratio}.`}
      </p>
    </div>
  );
}

function today(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

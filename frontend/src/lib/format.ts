import type { BandPosition, Money, PayReason } from "./types";

/** Amounts arrive as strings to keep them exact. Intl needs a number, and the
 *  conversion is safe here because this is the last step before display —
 *  nothing is computed from the result. */
export function money(value: Money, { compact = false } = {}): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: value.currency,
    maximumFractionDigits: 0,
    notation: compact ? "compact" : "standard",
  }).format(Number(value.amount));
}

export function day(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function month(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    month: "short",
    year: "numeric",
  });
}

export function count(value: number): string {
  return new Intl.NumberFormat("en-GB").format(value);
}

export function percent(value: number, of: number): string {
  if (!of) return "0%";
  return `${Math.round((value / of) * 100)}%`;
}

const REASON_LABELS: Record<PayReason, string> = {
  hire: "Starting salary",
  merit: "Merit",
  promotion: "Promotion",
  market_adjustment: "Market adjustment",
  correction: "Correction",
};

export function reason(value: PayReason): string {
  return REASON_LABELS[value] ?? value;
}

const POSITION_LABELS: Record<BandPosition, string> = {
  below: "Below band",
  within: "In band",
  above: "Above band",
};

export function position(value: BandPosition): string {
  return POSITION_LABELS[value];
}

/** Change between two amounts of the same currency, for a pay timeline. */
export function changeFrom(previous: Money, current: Money): string | null {
  const before = Number(previous.amount);
  const after = Number(current.amount);
  if (!before || before === after) return null;

  const delta = ((after - before) / before) * 100;
  return `${delta > 0 ? "+" : ""}${delta.toFixed(1)}%`;
}

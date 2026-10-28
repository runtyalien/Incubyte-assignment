import Link from "next/link";
import type { ReactNode } from "react";

import { count, position } from "@/lib/format";
import type { BandPosition } from "@/lib/types";

export function Page({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-muted">{description}</p>
          )}
        </div>
        {actions}
      </div>
      {children}
    </main>
  );
}

export function Card({
  title,
  hint,
  children,
  className = "",
}: {
  title?: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-line bg-surface ${className}`}
    >
      {title && (
        <div className="flex items-baseline justify-between gap-4 border-b border-line px-4 py-3">
          <h2 className="text-sm font-medium">{title}</h2>
          {hint && <span className="text-xs text-faint">{hint}</span>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="tnum mt-1 text-xl font-semibold tracking-tight">
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-faint">{hint}</div>}
    </div>
  );
}

const POSITION_STYLES: Record<BandPosition, string> = {
  below: "bg-below-soft text-below",
  within: "bg-within-soft text-within",
  above: "bg-above-soft text-above",
};

export function BandTag({ value }: { value: BandPosition | null }) {
  if (!value) return <span className="text-xs text-faint">No band</span>;

  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium whitespace-nowrap ${POSITION_STYLES[value]}`}
    >
      {position(value)}
    </span>
  );
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="px-4 py-16 text-center">
      <p className="text-sm font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted">{hint}</p>}
    </div>
  );
}

export function Problem({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-below/40 bg-below-soft px-4 py-3 text-sm text-below"
    >
      {message}
    </div>
  );
}

export function Pager({
  page,
  pageSize,
  total,
  href,
}: {
  page: number;
  pageSize: number;
  total: number;
  href: (page: number) => string;
}) {
  const last = Math.max(1, Math.ceil(total / pageSize));
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const upto = Math.min(page * pageSize, total);

  return (
    <div className="flex items-center justify-between gap-4 border-t border-line px-4 py-3 text-sm">
      <span className="tnum text-muted">
        {count(first)}–{count(upto)} of {count(total)}
      </span>

      <div className="flex items-center gap-1">
        <Step to={href(page - 1)} disabled={page <= 1} label="Previous" />
        <span className="tnum px-2 text-muted">
          {count(page)} / {count(last)}
        </span>
        <Step to={href(page + 1)} disabled={page >= last} label="Next" />
      </div>
    </div>
  );
}

function Step({
  to,
  disabled,
  label,
}: {
  to: string;
  disabled: boolean;
  label: string;
}) {
  const style = "rounded border border-line px-2.5 py-1";

  if (disabled) {
    return (
      <span aria-disabled className={`${style} text-faint`}>
        {label}
      </span>
    );
  }

  return (
    <Link href={to} className={`${style} hover:bg-accent-soft`}>
      {label}
    </Link>
  );
}

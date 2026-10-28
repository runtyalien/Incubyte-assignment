import Link from "next/link";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          )}
        </div>
        {actions}
      </div>
      {children}
    </main>
  );
}

/** A titled card. Named Panel so it does not shadow the library's Card, which
 *  it is built from. */
export function Panel({
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
    <Card className={`gap-0 overflow-hidden py-0 ${className}`}>
      {title && (
        <CardHeader className="flex items-baseline justify-between gap-4 border-b px-4 py-3">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {hint && <span className="text-xs text-faint">{hint}</span>}
        </CardHeader>
      )}
      <CardContent className="px-0">{children}</CardContent>
    </Card>
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
    <Card className="gap-0 px-4 py-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="tnum mt-1 text-xl font-semibold tracking-tight">
        {value}
      </div>
      {hint && <div className="mt-0.5 text-xs text-faint">{hint}</div>}
    </Card>
  );
}

const POSITION_STYLES: Record<BandPosition, string> = {
  below: "bg-below-soft text-below border-transparent",
  within: "bg-within-soft text-within border-transparent",
  above: "bg-above-soft text-above border-transparent",
};

export function BandTag({ value }: { value: BandPosition | null }) {
  if (!value) return <span className="text-xs text-faint">No band</span>;

  return (
    <Badge variant="outline" className={POSITION_STYLES[value]}>
      {position(value)}
    </Badge>
  );
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="px-4 py-16 text-center">
      <p className="text-sm font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function Problem({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive"
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
    <div className="flex items-center justify-between gap-4 border-t px-4 py-3 text-sm">
      <span className="tnum text-muted-foreground">
        {count(first)}–{count(upto)} of {count(total)}
      </span>

      <div className="flex items-center gap-2">
        <Step to={href(page - 1)} disabled={page <= 1} label="Previous" />
        <span className="tnum px-1 text-muted-foreground">
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
  if (disabled) {
    return (
      <Button variant="outline" size="sm" disabled aria-disabled>
        {label}
      </Button>
    );
  }

  // This Button has no asChild, so the link borrows its styling instead of
  // being wrapped in one.
  return (
    <Link href={to} className={buttonVariants({ variant: "outline", size: "sm" })}>
      {label}
    </Link>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { BandMeter } from "@/components/band-meter";
import { PayChangeForm } from "@/components/pay-change-form";
import { BandTag, Page as Shell, Panel, Problem, Stat } from "@/components/shell";
import { ApiError, getEmployee } from "@/lib/api";
import { changeFrom, day, money, reason } from "@/lib/format";
import type { EmployeeDetail, PayEntry } from "@/lib/types";
import { one, withParams, type Params } from "@/lib/search-params";

export default function EmployeePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Params>;
}) {
  return (
    <Suspense fallback={<Shell title="Loading…">{null}</Shell>}>
      <Detail params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function Detail({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Params>;
}) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const asOf = one(query, "as_of");

  let person: EmployeeDetail;
  try {
    person = await getEmployee(Number(id), asOf);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    return (
      <Shell title="Employee">
        <Problem
          message={
            error instanceof ApiError ? error.message : "Could not load them."
          }
        />
      </Shell>
    );
  }

  return (
    <Shell
      title={person.name}
      description={`${person.level} ${person.job_family} · ${person.department} · ${person.location}`}
      actions={
        <Link
          href={`/employees${withParams(query, {})}`}
          className="text-sm text-muted-foreground underline-offset-2 hover:underline"
        >
          ← All employees
        </Link>
      }
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat
              label={asOf ? "Salary as of" : "Current salary"}
              value={person.pay ? money(person.pay) : "Not started"}
              hint={
                person.pay_effective_from
                  ? `since ${day(person.pay_effective_from)}`
                  : undefined
              }
            />
            <Stat
              label="In base currency"
              value={person.base_pay ? money(person.base_pay) : "—"}
              hint="converted at the rate on the day"
            />
            <Stat
              label="Compa-ratio"
              value={person.compa_ratio ?? "—"}
              hint="against the band midpoint"
            />
          </div>

          <Panel
            title="Position in band"
            hint={`${person.level} ${person.job_family}, ${person.location}`}
          >
            {person.band ? (
              <BandMeter band={person.band} pay={person.pay} />
            ) : (
              <p className="px-4 py-6 text-sm text-muted-foreground">
                No band is defined for this role in this country, so there is
                nothing to compare the salary against.
              </p>
            )}
          </Panel>

          <Panel title="Pay history" hint={`${person.history.length} records`}>
            <Timeline history={person.history} />
          </Panel>
        </div>

        <div className="space-y-4">
          {!asOf && (
            <Panel title="Record a pay change">
              <PayChangeForm
                employeeId={person.id}
                currency={person.pay?.currency ?? "USD"}
                hiredOn={person.hired_on}
                current={person.pay?.amount ?? ""}
              />
            </Panel>
          )}

          <Panel title="Details">
            <dl className="divide-y divide-border text-sm">
              <Fact label="Staff number" value={person.staff_number} mono />
              <Fact label="Email" value={person.email} />
              <Fact label="Band position">
                <BandTag value={person.band_position} />
              </Fact>
              <Fact label="Hired" value={day(person.hired_on)} />
              {person.left_on && (
                <Fact label="Left" value={day(person.left_on)} />
              )}
            </dl>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

function Timeline({ history }: { history: PayEntry[] }) {
  if (history.length === 0) {
    return (
      <p className="px-4 py-6 text-sm text-muted-foreground">Nothing on record yet.</p>
    );
  }

  const today = new Date().toISOString().slice(0, 10);
  const newestFirst = [...history].reverse();

  return (
    <ol className="divide-y divide-border">
      {newestFirst.map((entry, index) => {
        const previous = newestFirst[index + 1];
        const delta = previous ? changeFrom(previous.amount, entry.amount) : null;
        const pending = entry.effective_from > today;

        return (
          <li
            key={`${entry.effective_from}-${index}`}
            className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3 text-sm"
          >
            <span className="tnum w-28 text-muted-foreground">
              {day(entry.effective_from)}
            </span>

            <span className="tnum w-32 font-medium">{money(entry.amount)}</span>

            <span
              className={`tnum w-14 text-xs ${
                delta?.startsWith("+") ? "text-within" : "text-muted-foreground"
              }`}
            >
              {delta}
            </span>

            <span className="text-muted-foreground">{reason(entry.reason)}</span>

            {pending && (
              <span className="rounded bg-above-soft px-1.5 py-0.5 text-xs text-above">
                Takes effect {day(entry.effective_from)}
              </span>
            )}

            {entry.note && (
              <span className="w-full text-xs text-faint">{entry.note}</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function Fact({
  label,
  value,
  mono,
  children,
}: {
  label: string;
  value?: string;
  mono?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-2.5">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={`text-right ${mono ? "tnum" : ""}`}>
        {children ?? value}
      </dd>
    </div>
  );
}

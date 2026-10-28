import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { BandMeter } from "@/components/band-meter";
import { PayChangeForm } from "@/components/pay-change-form";
import { BandTag, Card, Page as Shell, Problem, Stat } from "@/components/ui";
import { ApiError, getEmployee } from "@/lib/api";
import { changeFrom, day, money, reason } from "@/lib/format";
import type { EmployeeDetail, PayEntry } from "@/lib/types";

export default function EmployeePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<Shell title="Loading…">{null}</Shell>}>
      <Detail params={params} />
    </Suspense>
  );
}

async function Detail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let person: EmployeeDetail;
  try {
    person = await getEmployee(Number(id));
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
          href="/employees"
          className="text-sm text-muted underline-offset-2 hover:underline"
        >
          ← All employees
        </Link>
      }
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat
              label="Current salary"
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

          <Card
            title="Position in band"
            hint={`${person.level} ${person.job_family}, ${person.location}`}
          >
            {person.band ? (
              <BandMeter band={person.band} pay={person.pay} />
            ) : (
              <p className="px-4 py-6 text-sm text-muted">
                No band is defined for this role in this country, so there is
                nothing to compare the salary against.
              </p>
            )}
          </Card>

          <Card title="Pay history" hint={`${person.history.length} records`}>
            <Timeline history={person.history} />
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Record a pay change">
            <PayChangeForm
              employeeId={person.id}
              currency={person.pay?.currency ?? "USD"}
              hiredOn={person.hired_on}
              current={person.pay?.amount ?? ""}
            />
          </Card>

          <Card title="Details">
            <dl className="divide-y divide-line text-sm">
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
          </Card>
        </div>
      </div>
    </Shell>
  );
}

function Timeline({ history }: { history: PayEntry[] }) {
  if (history.length === 0) {
    return (
      <p className="px-4 py-6 text-sm text-muted">Nothing on record yet.</p>
    );
  }

  const today = new Date().toISOString().slice(0, 10);
  const newestFirst = [...history].reverse();

  return (
    <ol className="divide-y divide-line">
      {newestFirst.map((entry, index) => {
        const previous = newestFirst[index + 1];
        const delta = previous ? changeFrom(previous.amount, entry.amount) : null;
        const pending = entry.effective_from > today;

        return (
          <li
            key={`${entry.effective_from}-${index}`}
            className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3 text-sm"
          >
            <span className="tnum w-28 text-muted">
              {day(entry.effective_from)}
            </span>

            <span className="tnum w-32 font-medium">{money(entry.amount)}</span>

            <span
              className={`tnum w-14 text-xs ${
                delta?.startsWith("+") ? "text-within" : "text-muted"
              }`}
            >
              {delta}
            </span>

            <span className="text-muted">{reason(entry.reason)}</span>

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
      <dt className="text-muted">{label}</dt>
      <dd className={`text-right ${mono ? "tnum" : ""}`}>
        {children ?? value}
      </dd>
    </div>
  );
}

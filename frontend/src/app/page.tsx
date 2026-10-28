import Link from "next/link";
import { Suspense } from "react";

import { Filters } from "@/components/filters";
import { BandSplit, SpreadChart } from "@/components/spread-chart";
import { Page as Shell, Panel, Problem, Stat } from "@/components/shell";
import { ApiError, getDistribution, getOverview, getReference } from "@/lib/api";
import { count, day, money } from "@/lib/format";
import { toQuery, withParams, type Params } from "@/lib/search-params";

export default function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<Params>;
}) {
  return (
    <Shell
      title="How we pay"
      description="Where pay sits across the organisation, and who falls outside their band."
    >
      <Suspense fallback={<Loading />}>
        <Dashboard search={searchParams} />
      </Suspense>
    </Shell>
  );
}

async function Dashboard({ search }: { search: Promise<Params> }) {
  const params = await search;
  const filters = toQuery(params);

  let overview, byCountry, byLevel, byDepartment, reference;
  try {
    [overview, byCountry, byLevel, byDepartment, reference] = await Promise.all(
      [
        getOverview(filters),
        getDistribution("country", filters),
        getDistribution("level", filters),
        getDistribution("department", filters),
        getReference(),
      ],
    );
  } catch (error) {
    return (
      <Problem
        message={
          error instanceof ApiError
            ? error.message
            : "Something went wrong loading the figures."
        }
      />
    );
  }

  const outside = overview.band.below + overview.band.above;

  return (
    <>
      <Filters reference={reference} showPosition={false} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="People" value={count(overview.headcount)} />
        <Stat
          label="Annual payroll"
          value={money(overview.payroll, { compact: true })}
          hint="base salaries, in USD"
        />
        <Stat
          label="Median salary"
          value={money(overview.pay.median, { compact: true })}
          hint={`${money(overview.pay.p25, { compact: true })} – ${money(overview.pay.p75, { compact: true })} middle half`}
        />
        <Stat
          label="Median compa-ratio"
          value={overview.compa_median}
          hint="1.00 is the band midpoint"
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Panel
          title="Against band"
          hint={`${count(outside)} outside`}
          className="lg:col-span-1"
        >
          <BandSplit {...overview.band} />
          <div className="border-t border-border px-4 py-2.5 text-sm">
            <Link
              href={`/employees${withParams(params, {
                position: "below",
                sort: "compa",
                order: "asc",
              })}`}
              className="text-brand underline-offset-2 hover:underline"
            >
              See who is paid below their band →
            </Link>
          </div>
        </Panel>

        <Panel
          title="Pay by country"
          hint="USD, so countries compare"
          className="lg:col-span-2"
        >
          <SpreadChart groups={byCountry.groups} />
        </Panel>

        <Panel title="Pay by level" className="lg:col-span-2">
          <SpreadChart groups={byLevel.groups} />
        </Panel>

        <Panel title="Compa-ratio by department">
          <ul className="divide-y divide-border text-sm">
            {byDepartment.groups.map((group) => (
              <li
                key={group.key}
                className="flex items-baseline justify-between gap-3 px-4 py-2.5"
              >
                <span>
                  {group.label}
                  <span className="ml-2 text-xs text-faint">
                    {count(group.headcount)}
                  </span>
                </span>
                <span className="tnum font-medium">{group.compa_median}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <p className="mt-4 text-xs text-faint">
        As at {day(overview.as_of)}.
        {overview.unmeasured > 0 &&
          ` ${count(overview.unmeasured)} people are excluded: no pay in effect, or no band for their role.`}
        {" "}
        <Link
          href={`/employees${withParams(params, {})}`}
          className="underline-offset-2 hover:underline"
        >
          Open these filters in the directory
        </Link>
      </p>
    </>
  );
}

function Loading() {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-16 text-center text-sm text-muted-foreground">
      Working out the figures…
    </div>
  );
}

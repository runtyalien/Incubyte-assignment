import Link from "next/link";
import { Suspense } from "react";

import { Filters } from "@/components/filters";
import { BandTag, Card, Empty, Pager, Page as Shell, Problem } from "@/components/ui";
import { ApiError, getReference, listEmployees } from "@/lib/api";
import { count, day, money } from "@/lib/format";
import {
  one,
  pageNumber,
  toQuery,
  withParams,
  type Params,
} from "@/lib/search-params";
import type { EmployeeSummary } from "@/lib/types";

const PAGE_SIZE = 25;

const COLUMNS = [
  { key: "name", label: "Employee", sort: "name" },
  { key: "role", label: "Role", sort: "level" },
  { key: "location", label: "Location", sort: null },
  { key: "pay", label: "Salary", sort: "salary", right: true },
  { key: "compa", label: "Compa-ratio", sort: "compa", right: true },
  { key: "band", label: "Band", sort: null },
  { key: "hired", label: "Hired", sort: "hired", right: true },
] as const;

export default function EmployeesPage({
  searchParams,
}: {
  searchParams: Promise<Params>;
}) {
  return (
    <Shell
      title="Employees"
      description="Everyone on the payroll, with where their salary sits in band."
    >
      {/* The promise is passed down rather than awaited here: reading
          searchParams outside the boundary stops the shell prerendering. */}
      <Suspense fallback={<Loading />}>
        <Directory search={searchParams} />
      </Suspense>
    </Shell>
  );
}

async function Directory({ search }: { search: Promise<Params> }) {
  const params = await search;
  const page = pageNumber(params);
  const sort = one(params, "sort") ?? "name";
  const order = one(params, "order") ?? "asc";

  let data;
  let reference;
  try {
    [data, reference] = await Promise.all([
      listEmployees({
        ...toQuery(params),
        sort,
        order,
        page,
        page_size: PAGE_SIZE,
      }),
      getReference(),
    ]);
  } catch (error) {
    return (
      <Problem
        message={
          error instanceof ApiError
            ? error.message
            : "Something went wrong loading the directory."
        }
      />
    );
  }

  const link = (changes: Params) => `/employees${withParams(params, changes)}`;

  return (
    <>
      <Filters reference={reference} />

      <Card>
        {data.items.length === 0 ? (
          <Empty
            title="Nobody matches those filters"
            hint="Try widening the search or clearing a filter."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left">
                  {COLUMNS.map((column) => (
                    <th
                      key={column.key}
                      scope="col"
                      className={`px-4 py-2.5 font-medium whitespace-nowrap text-muted ${
                        "right" in column && column.right ? "text-right" : ""
                      }`}
                    >
                      {column.sort ? (
                        <SortLink
                          label={column.label}
                          field={column.sort}
                          active={sort === column.sort}
                          order={order}
                          href={link({
                            sort: column.sort,
                            order:
                              sort === column.sort && order === "asc"
                                ? "desc"
                                : "asc",
                          })}
                        />
                      ) : (
                        column.label
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((person) => (
                  <Row key={person.id} person={person} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <Pager
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          href={(next) => link({ page: String(next) })}
        />
      </Card>
    </>
  );
}

function Row({ person }: { person: EmployeeSummary }) {
  return (
    <tr className="border-b border-line last:border-0 hover:bg-accent-soft/40">
      <td className="px-4 py-2.5">
        <Link
          href={`/employees/${person.id}`}
          className="font-medium hover:underline"
        >
          {person.name}
        </Link>
        <div className="tnum text-xs text-faint">{person.staff_number}</div>
      </td>
      <td className="px-4 py-2.5">
        {person.level} {person.job_family}
        <div className="text-xs text-faint">{person.department}</div>
      </td>
      <td className="px-4 py-2.5 text-muted">{person.location}</td>
      <td className="tnum px-4 py-2.5 text-right">
        {person.pay ? (
          <>
            {money(person.pay)}
            {person.base_pay && person.pay.currency !== "USD" && (
              <div className="text-xs text-faint">
                {money(person.base_pay)}
              </div>
            )}
          </>
        ) : (
          <span className="text-faint">Not started</span>
        )}
      </td>
      <td className="tnum px-4 py-2.5 text-right">
        {person.compa_ratio ?? <span className="text-faint">—</span>}
      </td>
      <td className="px-4 py-2.5">
        <BandTag value={person.band_position} />
      </td>
      <td className="tnum px-4 py-2.5 text-right text-muted">
        {day(person.hired_on)}
        {person.left_on && (
          <div className="text-xs text-faint">left {day(person.left_on)}</div>
        )}
      </td>
    </tr>
  );
}

function SortLink({
  label,
  active,
  order,
  href,
}: {
  label: string;
  field: string;
  active: boolean;
  order: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-1 hover:text-foreground ${
        active ? "text-foreground" : ""
      }`}
      aria-sort={active ? (order === "asc" ? "ascending" : "descending") : undefined}
    >
      {label}
      <span aria-hidden className={active ? "" : "opacity-0"}>
        {order === "asc" ? "↑" : "↓"}
      </span>
    </Link>
  );
}

function Loading() {
  return (
    <Card>
      <div className="px-4 py-16 text-center text-sm text-muted">
        Loading {count(10000)} employees…
      </div>
    </Card>
  );
}

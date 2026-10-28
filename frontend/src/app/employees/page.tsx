import Link from "next/link";
import { Suspense } from "react";

import { Filters } from "@/components/filters";
import { BandTag, Empty, Pager, Page as Shell, Panel, Problem } from "@/components/shell";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  { key: "name", label: "Employee", sort: "name", right: false },
  { key: "role", label: "Role", sort: "level", right: false },
  { key: "location", label: "Location", sort: null, right: false },
  { key: "pay", label: "Salary", sort: "salary", right: true },
  { key: "compa", label: "Compa-ratio", sort: "compa", right: true },
  { key: "band", label: "Band", sort: null, right: false },
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

  const employeeHref = (id: number) =>
    `/employees/${id}${withParams(params, {})}`;

  return (
    <>
      <Filters reference={reference} />

      <Panel>
        {data.items.length === 0 ? (
          <Empty
            title="Nobody matches those filters"
            hint="Try widening the search or clearing a filter."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {COLUMNS.map((column) => (
                  <TableHead
                    key={column.key}
                    className={`whitespace-nowrap ${column.right ? "text-right" : ""}`}
                    aria-sort={
                      column.sort && sort === column.sort
                        ? order === "asc"
                          ? "ascending"
                          : "descending"
                        : undefined
                    }
                  >
                    {column.sort ? (
                      <SortLink
                        label={column.label}
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
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((person) => (
                <Row
                  key={person.id}
                  person={person}
                  href={employeeHref(person.id)}
                />
              ))}
            </TableBody>
          </Table>
        )}

        <Pager
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          href={(next) => link({ page: String(next) })}
        />
      </Panel>
    </>
  );
}

function Row({ person, href }: { person: EmployeeSummary; href: string }) {
  return (
    <TableRow>
      <TableCell>
        <Link
          href={href}
          className="font-medium hover:underline"
        >
          {person.name}
        </Link>
        <div className="tnum text-xs text-faint">{person.staff_number}</div>
      </TableCell>
      <TableCell>
        {person.level} {person.job_family}
        <div className="text-xs text-faint">{person.department}</div>
      </TableCell>
      <TableCell className="text-muted-foreground">{person.location}</TableCell>
      <TableCell className="tnum text-right">
        {person.pay ? (
          <>
            {money(person.pay)}
            {person.base_pay && person.pay.currency !== "USD" && (
              <div className="text-xs text-faint">{money(person.base_pay)}</div>
            )}
          </>
        ) : (
          <span className="text-faint">Not started</span>
        )}
      </TableCell>
      <TableCell className="tnum text-right">
        {person.compa_ratio ?? <span className="text-faint">—</span>}
      </TableCell>
      <TableCell>
        <BandTag value={person.band_position} />
      </TableCell>
      <TableCell className="tnum text-right text-muted-foreground">
        {day(person.hired_on)}
        {person.left_on && (
          <div className="text-xs text-faint">left {day(person.left_on)}</div>
        )}
      </TableCell>
    </TableRow>
  );
}

function SortLink({
  label,
  active,
  order,
  href,
}: {
  label: string;
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
    <Panel>
      <div className="px-4 py-16 text-center text-sm text-muted-foreground">
        Loading {count(10000)} employees…
      </div>
    </Panel>
  );
}

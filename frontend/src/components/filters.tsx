"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Reference } from "@/lib/types";

/** Radix refuses an empty string as a Select value, so "everything" needs a
 *  name of its own. It never reaches the URL. */
const ANY = "any";

const STATUSES = [
  { value: "active", label: "Current staff" },
  { value: "left", label: "Leavers" },
  { value: "all", label: "Everyone" },
];

const POSITIONS = [
  { value: "below", label: "Below band" },
  { value: "within", label: "In band" },
  { value: "above", label: "Above band" },
];

export function Filters({
  reference,
  showPosition = true,
  showStatus = true,
  showSearch = true,
}: {
  reference: Reference;
  showPosition?: boolean;
  showStatus?: boolean;
  showSearch?: boolean;
}) {
  const router = useRouter();
  const path = usePathname();
  const params = useSearchParams();
  const [pending, startTransition] = useTransition();

  const set = (changes: Record<string, string | undefined>) => {
    const next = new URLSearchParams(params.toString());

    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    // A filter change invalidates the page number: page 12 of a three-page
    // result is a blank screen.
    next.delete("page");

    startTransition(() => router.push(`${path}?${next.toString()}`));
  };

  const active = countActive(params);

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {showSearch && (
        <Search
          initial={params.get("q") ?? ""}
          onSearch={(value) => set({ q: value || undefined })}
        />
      )}

      <Pick
        label="Country"
        all="All countries"
        value={params.get("country")}
        options={reference.countries.map((c) => ({
          value: c.code,
          label: c.name,
        }))}
        onChange={(value) => set({ country: value })}
      />

      <Pick
        label="Department"
        all="All departments"
        value={params.get("department")}
        options={reference.departments.map((d) => ({ value: d, label: d }))}
        onChange={(value) => set({ department: value })}
      />

      <Pick
        label="Job family"
        all="All job families"
        value={params.get("family")}
        options={reference.families.map((f) => ({
          value: f,
          label: f,
        }))}
        onChange={(value) => set({ family: value })}
      />

      <Pick
        label="Level"
        all="All levels"
        value={params.get("level")}
        options={reference.levels.map((l) => ({
          value: l.code,
          label: l.code,
        }))}
        onChange={(value) => set({ level: value })}
        width="w-28"
      />

      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>As of</span>
        <Input
          aria-label="As of date"
          type="date"
          value={params.get("as_of") ?? ""}
          onChange={(event) => set({ as_of: event.target.value || undefined })}
          className="w-40"
        />
      </label>

      {showPosition && (
        <Pick
          label="Band position"
          all="Any band position"
          value={params.get("position")}
          options={POSITIONS}
          onChange={(value) => set({ position: value })}
        />
      )}

      {showStatus && (
        <Select
          items={STATUSES}
          value={params.get("status") ?? "active"}
          onValueChange={(value) =>
            set({ status: !value || value === "active" ? undefined : value })
          }
        >
          <SelectTrigger className="w-36" aria-label="Employment status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {active > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => startTransition(() => router.push(path))}
        >
          Clear {active} filter{active === 1 ? "" : "s"}
        </Button>
      )}

      {pending && (
        <span className="text-xs text-faint" aria-live="polite">
          Updating…
        </span>
      )}
    </div>
  );
}

function countActive(params: URLSearchParams): number {
  return [
    "q",
    "country",
    "department",
    "family",
    "level",
    "as_of",
    "position",
    "status",
  ].filter((key) => params.get(key)).length;
}

function Pick({
  label,
  all,
  value,
  options,
  onChange,
  width = "w-40",
}: {
  label: string;
  all: string;
  value: string | null;
  options: { value: string; label: string }[];
  onChange: (value: string | undefined) => void;
  width?: string;
}) {
  const items = [{ value: ANY, label: all }, ...options];

  return (
    <Select
      items={items}
      value={value ?? ANY}
      onValueChange={(next) => onChange(!next || next === ANY ? undefined : next)}
    >
      <SelectTrigger className={width} aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ANY}>{all}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function Search({
  initial,
  onSearch,
}: {
  initial: string;
  onSearch: (value: string) => void;
}) {
  const [text, setText] = useState(initial);
  const [lastFromUrl, setLastFromUrl] = useState(initial);

  // The URL can change from elsewhere — Clear, or the back button — and the
  // box has to follow. Adjusted during render rather than in an effect: an
  // effect would render once with the stale text and again with the new.
  // Remounting on a key would reset it mid-debounce and steal focus.
  if (initial !== lastFromUrl) {
    setLastFromUrl(initial);
    setText(initial);
  }

  // Typing shouldn't fire a request per keystroke across 10,000 rows.
  useEffect(() => {
    if (text === initial) return;
    const timer = setTimeout(() => onSearch(text.trim()), 300);
    return () => clearTimeout(timer);
    // onSearch is rebuilt each render; depending on it would reset the timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return (
    <Input
      type="search"
      value={text}
      onChange={(event) => setText(event.target.value)}
      placeholder="Name, staff number or email"
      aria-label="Search employees"
      className="w-56"
    />
  );
}

"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import type { Reference } from "@/lib/types";

const STATUSES = [
  { value: "active", label: "Current staff" },
  { value: "left", label: "Leavers" },
  { value: "all", label: "Everyone" },
];

const POSITIONS = [
  { value: "", label: "Any band position" },
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

      <Select
        label="Country"
        value={params.get("country") ?? ""}
        options={reference.countries.map((c) => ({
          value: c.code,
          label: c.name,
        }))}
        onChange={(value) => set({ country: value })}
      />

      <Select
        label="Department"
        value={params.get("department") ?? ""}
        options={reference.departments.map((d) => ({ value: d, label: d }))}
        onChange={(value) => set({ department: value })}
      />

      <Select
        label="Level"
        value={params.get("level") ?? ""}
        options={reference.levels.map((l) => ({
          value: l.code,
          label: l.code,
        }))}
        onChange={(value) => set({ level: value })}
      />

      {showPosition && (
        <Select
          label={POSITIONS[0].label}
          value={params.get("position") ?? ""}
          options={POSITIONS.slice(1)}
          onChange={(value) => set({ position: value })}
        />
      )}

      {showStatus && (
        <select
          aria-label="Employment status"
          value={params.get("status") ?? "active"}
          onChange={(event) =>
            set({
              status:
                event.target.value === "active"
                  ? undefined
                  : event.target.value,
            })
          }
          className="rounded border border-line bg-surface px-2 py-1.5 text-sm"
        >
          {STATUSES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}

      {active > 0 && (
        <button
          type="button"
          onClick={() => startTransition(() => router.push(path))}
          className="rounded px-2 py-1.5 text-sm text-muted underline-offset-2 hover:underline"
        >
          Clear {active} filter{active === 1 ? "" : "s"}
        </button>
      )}

      {pending && <span className="text-xs text-faint">Updating…</span>}
    </div>
  );
}

function countActive(params: URLSearchParams): number {
  return ["q", "country", "department", "family", "level", "position", "status"]
    .filter((key) => params.get(key))
    .length;
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string | undefined) => void;
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(event) => onChange(event.target.value || undefined)}
      className="rounded border border-line bg-surface px-2 py-1.5 text-sm"
    >
      <option value="">{label}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
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
    <input
      type="search"
      value={text}
      onChange={(event) => setText(event.target.value)}
      placeholder="Name, staff number or email"
      aria-label="Search employees"
      className="w-64 rounded border border-line bg-surface px-2.5 py-1.5 text-sm placeholder:text-faint"
    />
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/employees", label: "Employees" },
];

/** The bar itself, with no runtime-only data in it, so it can prerender. */
export function NavBar({ active }: { active: string | null }) {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-7xl items-center gap-8 px-6 py-3">
        <Link href="/" className="text-sm font-semibold tracking-tight">
          ACME <span className="text-muted font-normal">Salary</span>
        </Link>

        <nav className="flex gap-1 text-sm">
          {LINKS.map((link) => {
            const current =
              active === null
                ? false
                : link.href === "/"
                  ? active === "/"
                  : active.startsWith(link.href);

            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={current ? "page" : undefined}
                className={`rounded px-3 py-1.5 transition-colors ${
                  current
                    ? "bg-accent-soft text-accent font-medium"
                    : "text-muted hover:text-foreground"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto text-xs text-faint">
          Signed in as HR Manager
        </div>
      </div>
    </header>
  );
}

/** Which link is current is only known at runtime, so this half sits behind a
 *  Suspense boundary — otherwise it blocks every route from prerendering. */
export function Nav() {
  return <NavBar active={usePathname()} />;
}

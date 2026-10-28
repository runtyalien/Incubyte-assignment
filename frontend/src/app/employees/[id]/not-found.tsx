import Link from "next/link";

import { Page as Shell } from "@/components/shell";

export default function NotFound() {
  return (
    <Shell title="No such employee">
      <p className="text-sm text-muted-foreground">
        That staff record does not exist. It may have been removed, or the link
        may be wrong.
      </p>
      <Link
        href="/employees"
        className="mt-4 inline-block text-sm text-brand underline-offset-2 hover:underline"
      >
        Back to the directory →
      </Link>
    </Shell>
  );
}

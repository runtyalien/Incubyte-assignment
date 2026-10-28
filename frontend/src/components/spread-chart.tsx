import { count, money } from "@/lib/format";
import type { GroupStats, Money } from "@/lib/types";

/** Pay spread per group: the quartile range as a bar, the median as a mark.
 *
 *  A plain bar chart of medians throws away the thing an HR manager is
 *  actually asking — how wide the range is. Two departments on the same median
 *  with very different spreads are not paying people the same way.
 *
 *  Drawn with divs rather than a chart library: one shape, one axis, and the
 *  numbers are in the row anyway for anyone who needs them exactly.
 */
export function SpreadChart({
  groups,
  compact = false,
}: {
  groups: GroupStats[];
  compact?: boolean;
}) {
  if (groups.length === 0) {
    return <p className="px-4 py-8 text-sm text-muted">Nothing to show.</p>;
  }

  // One scale across every group, or the bars are not comparable.
  const ceiling = Math.max(
    ...groups.map((group) => Number(group.pay.p75.amount)),
  );
  const floor = Math.min(
    ...groups.map((group) => Number(group.pay.p25.amount)),
  );
  const span = ceiling - floor || 1;
  const at = (value: number) => ((value - floor) / span) * 100;
  const currency = groups[0].pay.median.currency;

  return (
    <div className="divide-y divide-line">
      {groups.map((group) => {
        const p25 = Number(group.pay.p25.amount);
        const p75 = Number(group.pay.p75.amount);
        const median = Number(group.pay.median.amount);

        return (
          <div
            key={group.key}
            className="grid grid-cols-[6rem_1fr_7rem] items-center gap-3 px-4 py-2.5 text-sm"
          >
            <div>
              <div className="font-medium">{group.key}</div>
              {!compact && (
                <div className="text-xs text-faint">
                  {count(group.headcount)}
                </div>
              )}
            </div>

            <div
              className="relative h-6"
              title={`${money(group.pay.p25)} – ${money(group.pay.p75)}, median ${money(group.pay.median)}`}
            >
              <div className="absolute top-2.5 h-1 w-full rounded bg-line" />
              <div
                className="absolute top-1.5 h-3 rounded bg-accent-soft"
                style={{
                  left: `${at(p25)}%`,
                  width: `${Math.max(at(p75) - at(p25), 0.8)}%`,
                }}
              />
              <div
                className="absolute top-0.5 h-5 w-0.5 rounded bg-accent"
                style={{ left: `${at(median)}%` }}
              />
            </div>

            <div className="tnum text-right font-medium">
              {money(group.pay.median, { compact: true })}
            </div>
          </div>
        );
      })}

      <div className="flex justify-between px-4 py-2 text-xs text-faint">
        <span>Bar spans the middle half. The line is the median.</span>
        <span className="tnum">
          scale {money(scaleLabel(floor, currency), { compact: true })} –{" "}
          {money(scaleLabel(ceiling, currency), { compact: true })}
        </span>
      </div>
    </div>
  );
}

function scaleLabel(amount: number, currency: string): Money {
  return { amount: String(amount), currency };
}

/** How a population splits across the three band positions. */
export function BandSplit({
  below,
  within,
  above,
}: {
  below: number;
  within: number;
  above: number;
}) {
  const total = below + within + above || 1;
  const parts = [
    { label: "Below band", value: below, bar: "bg-below", text: "text-below" },
    { label: "In band", value: within, bar: "bg-within", text: "text-within" },
    { label: "Above band", value: above, bar: "bg-above", text: "text-above" },
  ];

  return (
    <div className="px-4 py-4">
      <div className="flex h-2.5 overflow-hidden rounded-full bg-line">
        {parts.map((part) => (
          <div
            key={part.label}
            className={part.bar}
            style={{ width: `${(part.value / total) * 100}%` }}
          />
        ))}
      </div>

      <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
        {parts.map((part) => (
          <div key={part.label}>
            <dt className="text-xs text-muted">{part.label}</dt>
            <dd className={`tnum font-medium ${part.text}`}>
              {count(part.value)}
              <span className="ml-1 text-xs font-normal text-faint">
                {Math.round((part.value / total) * 100)}%
              </span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

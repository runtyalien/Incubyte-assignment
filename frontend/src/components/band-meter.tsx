import { money } from "@/lib/format";
import type { Band, Money } from "@/lib/types";

/** Where a salary sits in its band.
 *
 *  The scale is padded past whichever is wider, the band or the salary, so
 *  someone paid outside their range still appears on the chart instead of
 *  being clipped to the edge — which is the one case worth looking at.
 */
export function BandMeter({ band, pay }: { band: Band; pay: Money | null }) {
  const low = Number(band.low.amount);
  const high = Number(band.high.amount);
  const mid = Number(band.mid.amount);
  const current = pay ? Number(pay.amount) : null;

  const floor = Math.min(low, current ?? low) * 0.94;
  const ceiling = Math.max(high, current ?? high) * 1.06;
  const span = ceiling - floor || 1;
  const at = (value: number) => ((value - floor) / span) * 100;

  return (
    <div className="px-4 py-5">
      <div className="relative h-11">
        {/* The full scale. */}
        <div className="absolute top-4 h-2.5 w-full rounded-full bg-line" />

        {/* The band itself. */}
        <div
          className="absolute top-4 h-2.5 rounded-full bg-accent-soft"
          style={{ left: `${at(low)}%`, width: `${at(high) - at(low)}%` }}
        />

        {/* Midpoint: what the role is meant to pay. */}
        <div
          className="absolute top-3 h-4.5 w-px bg-accent"
          style={{ left: `${at(mid)}%` }}
          aria-hidden
        />

        {current !== null && (
          <div
            className="absolute top-1.5 flex -translate-x-1/2 flex-col items-center"
            style={{ left: `${at(current)}%` }}
          >
            <div className="tnum mb-0.5 text-xs font-medium whitespace-nowrap">
              {money(pay!)}
            </div>
            <div className="h-3.5 w-1 rounded-full bg-foreground" />
          </div>
        )}
      </div>

      <div className="tnum mt-1 flex justify-between text-xs text-faint">
        <span>{money(band.low)}</span>
        <span className="text-muted">mid {money(band.mid)}</span>
        <span>{money(band.high)}</span>
      </div>
    </div>
  );
}

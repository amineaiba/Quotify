import { Badge, type BadgeTone } from "../../components/Badge";
import type { QuoteSummary } from "../../lib/conversations";
import { formatPrice } from "../../lib/format";

const STATUS: Record<QuoteSummary["status"], { label: string; tone: BadgeTone }> = {
  auto_sent: { label: "Auto-sent", tone: "ok" },
  approved: { label: "Approved", tone: "ok" },
  pending: { label: "Pending review", tone: "warn" },
  rejected: { label: "Rejected", tone: "alert" },
};

export function ThreadQuoteCard({ quote }: { quote: QuoteSummary }) {
  const status = STATUS[quote.status];
  return (
    <div className="w-full overflow-hidden rounded-xl border border-line-strong bg-surface">
      <div className="flex items-center justify-between gap-2.5 border-b border-line px-3.5 py-2.5">
        <span className="text-xs font-semibold text-ink-2">Quote</span>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      <div className="py-1">
        {quote.lines.map((line) => (
          <div
            key={line.item_id}
            className="flex items-baseline justify-between gap-3.5 px-3.5 py-1.5"
          >
            <span className="min-w-0 text-[12.5px] leading-snug text-ink-2">
              {line.name} · {line.quantity} {line.unit}
            </span>
            <span className="font-mono text-[12.5px] font-medium">{formatPrice(line.total)}</span>
          </div>
        ))}
      </div>
      <div className="flex items-baseline justify-between gap-3.5 border-t border-line-strong bg-surface-3 px-3.5 py-2.5">
        <span className="text-xs font-semibold">Subtotal</span>
        <span className="font-mono text-[17px] font-semibold">{formatPrice(quote.subtotal)}</span>
      </div>
    </div>
  );
}

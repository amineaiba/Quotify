import { Link } from "react-router-dom";
import { Badge, type BadgeTone } from "../../components/Badge";
import type { QuoteListItem, QuoteStatus } from "../../lib/quotes";
import { formatDateTime, formatPrice, initials } from "../../lib/format";

const STATUS: Record<QuoteStatus, { label: string; tone: BadgeTone }> = {
  auto_sent: { label: "Auto-sent", tone: "ok" },
  approved: { label: "Approved", tone: "ok" },
  pending: { label: "Pending review", tone: "warn" },
  rejected: { label: "Rejected", tone: "alert" },
};

function QuoteRow({ quote }: { quote: QuoteListItem }) {
  const status = STATUS[quote.status];
  return (
    <Link
      to={`/inbox/${quote.conversation_id}`}
      className="flex items-center gap-3 border-b border-line px-4 py-3.5 last:border-b-0 hover:bg-surface-2"
    >
      <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full border border-line bg-surface-2 text-[11px] font-semibold text-ink-2">
        {initials(quote.client.name, quote.client.phone_number)}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-[13px] font-semibold">
          {quote.client.name ?? quote.client.phone_number}
        </span>
        <span className="truncate text-xs text-ink-3">{quote.draft_message}</span>
      </div>
      <div className="flex flex-none flex-col items-end gap-1">
        <span className="font-mono text-[13px] font-semibold">
          {quote.subtotal !== null ? formatPrice(quote.subtotal) : "—"}
        </span>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      <span className="hidden flex-none font-mono text-xs text-ink-3 sm:block">
        {formatDateTime(quote.created_at)}
      </span>
    </Link>
  );
}

export function QuoteHistoryList({ quotes }: { quotes: QuoteListItem[] }) {
  if (quotes.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1.5 rounded-[14px] border border-dashed border-line-strong bg-surface px-6 py-14 text-center">
        <span className="text-sm font-medium text-ink-2">Nothing here</span>
        <span className="text-sm text-ink-3">Sent and reviewed quotes will show up here.</span>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow)]">
      {quotes.map((quote) => (
        <QuoteRow key={quote.id} quote={quote} />
      ))}
    </div>
  );
}

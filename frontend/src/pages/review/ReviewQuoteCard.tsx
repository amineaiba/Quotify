import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { ApiError } from "../../lib/api";
import { formatPrice, initials } from "../../lib/format";
import { quotesApi, type HoldReason, type QuoteListItem } from "../../lib/quotes";

const HOLD_REASON_LABEL: Record<HoldReason, string> = {
  low_confidence: "Low confidence",
  rate_limited: "Rate limited",
};

export function ReviewQuoteCard({ quote }: { quote: QuoteListItem }) {
  const [message, setMessage] = useState(quote.draft_message);
  const queryClient = useQueryClient();

  const approve = useMutation({
    mutationFn: () => quotesApi.approve(quote.id, message),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotes"] }),
  });

  const reject = useMutation({
    mutationFn: () => quotesApi.reject(quote.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quotes"] }),
  });

  const busy = approve.isPending || reject.isPending;
  const error = approve.error ?? reject.error;

  return (
    <div className="overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow)]">
      <div className="flex items-center gap-3 border-b border-line px-4 py-3.5">
        <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full border border-line bg-surface-2 text-[11px] font-semibold text-ink-2">
          {initials(quote.client.name, quote.client.phone_number)}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="truncate text-[13px] font-semibold">
            {quote.client.name ?? quote.client.phone_number}
          </span>
          <span className="truncate font-mono text-xs text-ink-3">{quote.client.phone_number}</span>
        </div>
        {quote.hold_reason && <Badge tone="warn">{HOLD_REASON_LABEL[quote.hold_reason]}</Badge>}
      </div>

      <div className="flex flex-col gap-3 px-4 py-3.5">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={3}
          disabled={busy}
          className="w-full resize-none rounded-lg border border-line-strong bg-transparent px-3 py-2 text-sm leading-snug focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        />

        {quote.lines.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-line">
            {quote.lines.map((line) => (
              <div
                key={line.item_id}
                className="flex items-baseline justify-between gap-3.5 border-b border-line px-3.5 py-1.5 last:border-b-0"
              >
                <span className="min-w-0 text-[12.5px] leading-snug text-ink-2">
                  {line.name} · {line.quantity} {line.unit}
                </span>
                <span className="font-mono text-[12.5px] font-medium">
                  {formatPrice(line.total)}
                </span>
              </div>
            ))}
            {quote.subtotal !== null && (
              <div className="flex items-baseline justify-between gap-3.5 bg-surface-3 px-3.5 py-2.5">
                <span className="text-xs font-semibold">Subtotal</span>
                <span className="font-mono text-[15px] font-semibold">
                  {formatPrice(quote.subtotal)}
                </span>
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="text-sm text-alert">
            {error instanceof ApiError ? error.detail : "Something went wrong. Try again."}
          </p>
        )}

        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            disabled={busy || message.trim().length === 0}
            onClick={() => approve.mutate()}
          >
            {approve.isPending ? "Approving…" : "Approve & send"}
          </Button>
          <Button variant="secondary" size="sm" disabled={busy} onClick={() => reject.mutate()}>
            {reject.isPending ? "Rejecting…" : "Reject"}
          </Button>
        </div>
      </div>
    </div>
  );
}

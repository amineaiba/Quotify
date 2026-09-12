import { Link } from "react-router-dom";
import { Badge, type BadgeTone } from "../../components/Badge";
import type { ConversationSummary } from "../../lib/conversations";
import { formatDateTime, formatPrice, initials } from "../../lib/format";

const STATUS: Record<ConversationSummary["status"], { label: string; tone: BadgeTone }> = {
  auto_sent: { label: "Auto-sent", tone: "ok" },
  held: { label: "Held", tone: "warn" },
  attention: { label: "Attention", tone: "alert" },
};

function ConversationRow({ conversation }: { conversation: ConversationSummary }) {
  const status = STATUS[conversation.status];
  return (
    <Link
      to={`/inbox/${conversation.id}`}
      className="flex items-center gap-3 border-b border-line px-4 py-3.5 last:border-b-0 hover:bg-surface-2"
    >
      <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full border border-line bg-surface-2 text-[11px] font-semibold text-ink-2">
        {initials(conversation.client.name, conversation.client.phone_number)}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-[13px] font-semibold">
          {conversation.client.name ?? conversation.client.phone_number}
        </span>
        <span className="truncate text-xs text-ink-3">
          {conversation.last_message?.content ?? "No messages yet"}
        </span>
      </div>
      <div className="flex flex-none flex-col items-end gap-1">
        <span className="font-mono text-[13px] font-semibold">
          {conversation.total !== null ? formatPrice(conversation.total) : "—"}
        </span>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      {conversation.last_message && (
        <span className="hidden flex-none font-mono text-xs text-ink-3 sm:block">
          {formatDateTime(conversation.last_message.created_at)}
        </span>
      )}
    </Link>
  );
}

export function ConversationsList({ conversations }: { conversations: ConversationSummary[] }) {
  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1.5 rounded-[14px] border border-dashed border-line-strong bg-surface px-6 py-14 text-center">
        <span className="text-sm font-medium text-ink-2">Nothing here</span>
        <span className="text-sm text-ink-3">Conversations will show up as clients write in.</span>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow)]">
      {conversations.map((conversation) => (
        <ConversationRow key={conversation.id} conversation={conversation} />
      ))}
    </div>
  );
}

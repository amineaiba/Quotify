import type { Message } from "../../lib/conversations";
import { formatDateTime } from "../../lib/format";

export function ThreadMessages({ messages }: { messages: Message[] }) {
  if (messages.length === 0) {
    return <p className="text-sm text-ink-3">No messages yet.</p>;
  }

  return (
    <div className="flex flex-col gap-2.5 rounded-[14px] border border-line bg-surface-3 p-4">
      {messages.map((message) => {
        const fromClient = message.sender === "client";
        return (
          <div
            key={message.id}
            className={`max-w-[86%] rounded-xl border border-line px-3 pb-1.5 pt-2.5 text-[13.5px] leading-relaxed ${
              fromClient
                ? "self-start bg-surface"
                : "self-end bg-[color-mix(in_oklab,var(--accent)_10%,var(--surface))]"
            }`}
          >
            {message.content}
            <span className="mt-0.5 block text-right font-mono text-[10px] text-ink-3">
              {formatDateTime(message.created_at)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

import type { ConversationFilter } from "../../lib/conversations";

const TABS: { value: ConversationFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "needs_attention", label: "Needs attention" },
  { value: "auto_sent", label: "Auto-sent" },
];

export function ConversationsFilterTabs({
  active,
  onChange,
}: {
  active: ConversationFilter;
  onChange: (filter: ConversationFilter) => void;
}) {
  return (
    <div className="flex gap-1.5">
      {TABS.map((tab) => (
        <button
          key={tab.value}
          type="button"
          onClick={() => onChange(tab.value)}
          className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors duration-150 ${
            active === tab.value
              ? "border-accent bg-accent text-accent-on"
              : "border-line-strong bg-transparent text-ink-2 hover:bg-surface-2"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

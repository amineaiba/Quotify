import { Link } from "react-router-dom";
import { Badge, type BadgeTone } from "../../components/Badge";

const STATUS_TONE: Record<string, BadgeTone> = { auto: "ok", review: "warn", attention: "alert" };

const ROWS = [
  { initials: "AB", name: "Amine Belkacem", snippet: "Faïence 6 m² + pose", total: "46 800 DA", status: "auto", label: "Auto-sent" },
  { initials: "SH", name: "Sofiane Haddad", snippet: "Peinture 2 chambres", total: "88 200 DA", status: "review", label: "Held" },
  { initials: "YC", name: "Yasmine Cherif", snippet: "Fuite sous l'évier", total: "—", status: "attention", label: "Attention" },
];

/** Mock preview of the real inbox — landing page only, not wired to the API. */
export function InboxPreview() {
  return (
    <div className="mt-1 overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow)] min-[860px]:mt-[clamp(4px,3vw,34px)]">
      <div className="flex items-center gap-2.5 border-b border-line bg-surface-3 px-4 py-3.5">
        <span className="h-2 w-2 flex-none rounded-full bg-ok" />
        <span className="text-[13px] font-semibold">Conversations</span>
        <span className="ml-auto font-mono text-xs text-ink-3">3 new · 09:42</span>
      </div>
      {ROWS.map((row) => (
        <div key={row.initials} className="flex items-center gap-3 border-b border-line px-4 py-3.5">
          <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full border border-line bg-surface-2 text-[11px] font-semibold text-ink-2">
            {row.initials}
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="truncate text-[13px] font-semibold">{row.name}</span>
            <span className="truncate text-xs text-ink-3">{row.snippet}</span>
          </div>
          <div className="flex flex-none flex-col items-end gap-1">
            <span className="font-mono text-[13px] font-semibold">{row.total}</span>
            <Badge tone={STATUS_TONE[row.status]}>{row.label}</Badge>
          </div>
        </div>
      ))}
      <div className="flex items-center gap-2 px-4 py-2.5">
        <span className="font-mono text-[11px] text-ink-3">Live view from the dashboard</span>
        <Link to="/inbox" className="ml-auto text-xs font-semibold text-accent underline">
          Open
        </Link>
      </div>
    </div>
  );
}

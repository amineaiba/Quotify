import { Badge } from "../../components/Badge";

const MESSAGES = [
  { align: "start", text: "Salam, ndir faïence f salle de bain, chhal taswa ?", time: "09:31" },
  {
    align: "end",
    text: "Bonjour ! Il me faut la surface en m², et si vous voulez la fourniture ou seulement la pose.",
    time: "09:32",
  },
  { align: "start", text: "6 m² à peu près. Faïence 20×20 + la pose, kolch.", time: "09:38" },
] as const;

const QUOTE_LINES = [
  { name: "Faïence 20×20 · 6,5 m²", amount: "15 600 DA" },
  { name: "Pose · 6,5 m²", amount: "11 700 DA" },
  { name: "Colle, joints, main d'œuvre", amount: "10 850 DA" },
];

/** Mock preview of a real thread + quote — landing page only, not wired to the API. */
export function ThreadPreview() {
  return (
    <div className="overflow-hidden rounded-[14px] border border-line bg-surface shadow-[var(--shadow)]">
      <div className="flex items-center gap-2.5 border-b border-line px-4 py-3.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-surface-2 text-[11px] font-semibold text-ink-2">
          AB
        </div>
        <div className="flex min-w-0 flex-col gap-0.5">
          <span className="text-[13px] font-semibold">Amine Belkacem</span>
          <span className="font-mono text-[11px] text-ink-3">+213 661 24 88 10 · WhatsApp</span>
        </div>
      </div>

      <div className="flex flex-col gap-2.5 bg-surface-3 p-4">
        {MESSAGES.map((m) => (
          <div
            key={m.time}
            className={`max-w-[86%] rounded-xl border border-line px-3 pb-1.5 pt-2.5 text-[13.5px] leading-relaxed ${
              m.align === "end"
                ? "self-end bg-[color-mix(in_oklab,var(--accent)_10%,var(--surface))]"
                : "self-start bg-surface"
            }`}
          >
            {m.text}
            <span className="mt-0.5 block text-right font-mono text-[10px] text-ink-3">
              {m.time}
            </span>
          </div>
        ))}

        <div className="mt-0.5 w-full self-end overflow-hidden rounded-xl border border-line-strong bg-surface">
          <div className="flex items-center justify-between gap-2.5 border-b border-line px-3.5 py-2.5">
            <span className="font-mono text-[11px] font-semibold">DEV-2026-0418</span>
            <Badge tone="ok">Auto-sent</Badge>
          </div>
          <div className="py-1">
            {QUOTE_LINES.map((line) => (
              <div
                key={line.name}
                className="flex items-baseline justify-between gap-3.5 px-3.5 py-1.5"
              >
                <span className="min-w-0 text-[12.5px] leading-snug text-ink-2">{line.name}</span>
                <span className="font-mono text-[12.5px] font-medium">{line.amount}</span>
              </div>
            ))}
          </div>
          <div className="flex items-baseline justify-between gap-3.5 border-t border-line-strong bg-surface-3 px-3.5 py-2.5">
            <span className="text-xs font-semibold">Total TTC</span>
            <span className="font-mono text-[17px] font-semibold">46 800 DA</span>
          </div>
          <div className="px-3.5 pb-2.5 text-right">
            <span className="font-mono text-[10px] text-ink-3">Sent automatically · 09:42</span>
          </div>
        </div>
      </div>
    </div>
  );
}

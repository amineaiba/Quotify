import type { ReactNode } from "react";

export type BadgeTone = "ok" | "warn" | "alert" | "sent" | "neutral";

const TONE_CLASSES: Record<BadgeTone, string> = {
  ok: "text-ok bg-[color-mix(in_oklab,var(--ok)_10%,var(--surface))] border-[color-mix(in_oklab,var(--ok)_28%,var(--surface))]",
  warn: "text-warn bg-[color-mix(in_oklab,var(--warn)_12%,var(--surface))] border-[color-mix(in_oklab,var(--warn)_30%,var(--surface))]",
  alert: "text-alert bg-[color-mix(in_oklab,var(--alert)_10%,var(--surface))] border-[color-mix(in_oklab,var(--alert)_28%,var(--surface))]",
  sent: "text-ink-2 bg-surface-3 border-line-strong",
  neutral: "text-ink-3 bg-transparent border-line",
};

/** Status pill. `neutral` gets a hollow dot (resting state); every other tone is filled. */
export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      <span
        className={
          tone === "neutral"
            ? "h-1.5 w-1.5 rounded-full shadow-[inset_0_0_0_1.5px_currentColor]"
            : "h-1.5 w-1.5 rounded-full bg-current"
        }
      />
      {children}
    </span>
  );
}

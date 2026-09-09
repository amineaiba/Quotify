import { LinkButton } from "../../components/Button";
import { InboxPreview } from "./InboxPreview";

export function Hero() {
  return (
    <section className="mx-auto w-full max-w-[1240px] px-4 py-[clamp(38px,6vw,78px)] sm:px-[clamp(18px,5vw,60px)]">
      <div className="grid grid-cols-1 items-start gap-[clamp(30px,5vw,60px)] min-[860px]:grid-cols-[1.12fr_0.92fr]">
        <div className="flex max-w-[640px] flex-col gap-5 motion-safe:opacity-0 motion-safe:animate-[fade-up_0.6s_ease-out_forwards]">
          <div className="flex items-center gap-3">
            <span className="font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-3">
              Devis WhatsApp · Algérie
            </span>
            <span className="h-px max-w-[90px] flex-1 bg-line-strong" />
          </div>
          <h1 className="max-w-[15ch] font-serif text-[clamp(38px,5.4vw,66px)] font-medium leading-[1.08] tracking-tight">
            Your clients write. Quotify answers with a price.
          </h1>
          <p className="max-w-[52ch] text-[clamp(15px,2.1vw,18px)] leading-relaxed text-ink-2">
            It reads WhatsApp messages in French and Darja, asks for what's missing, checks your
            catalog, and sends the quote automatically.
          </p>
          <div className="flex flex-wrap gap-2.5 pt-0.5">
            <LinkButton to="/login" variant="primary">
              Start quoting
            </LinkButton>
            <LinkButton to="/inbox" variant="secondary">
              See the dashboard
            </LinkButton>
          </div>
          <p className="max-w-[46ch] border-l-2 border-accent py-0.5 pl-4 text-sm leading-relaxed text-ink-2">
            A vague request, an item outside your catalog, or a quote above your limit — it waits
            for you instead of guessing.
          </p>
        </div>

        <InboxPreview />
      </div>
    </section>
  );
}

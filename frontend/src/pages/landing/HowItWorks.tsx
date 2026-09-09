import { ThreadPreview } from "./ThreadPreview";

const STEPS = [
  {
    n: "01",
    title: "The client writes",
    body: "A message lands on WhatsApp — French, Darja, or both in the same sentence. Nothing for you to set up.",
  },
  {
    n: "02",
    title: "Quotify fills the gaps",
    body: "It asks for the surface, the quantity, whether you supply the materials. Only what it needs to price the job, nothing else.",
  },
  {
    n: "03",
    title: "The quote goes out",
    body: "Priced from your own catalog and quantity tiers, sent back in the same thread, logged in your history.",
  },
];

export function HowItWorks() {
  return (
    <section className="border-y border-line bg-surface-3">
      <div className="mx-auto w-full max-w-[1240px] px-4 py-[clamp(42px,6vw,76px)] sm:px-[clamp(18px,5vw,60px)]">
        <div className="grid grid-cols-1 items-start gap-[clamp(32px,5vw,64px)] min-[860px]:grid-cols-[0.95fr_1.05fr]">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-3">
              <span className="font-mono text-[11px] font-medium uppercase tracking-[0.1em] text-ink-3">
                How it works
              </span>
              <h2 className="max-w-[16ch] font-serif text-[clamp(27px,3.6vw,38px)] font-medium leading-[1.12] tracking-tight">
                One message in, one price out.
              </h2>
            </div>
            <div className="flex flex-col">
              {STEPS.map((step) => (
                <div
                  key={step.n}
                  className="relative border-l border-line-strong pb-6 pl-[34px] last:border-transparent last:pb-0"
                >
                  <span className="absolute -left-[13px] top-0 flex h-[26px] w-[26px] items-center justify-center rounded-[7px] border border-line-strong bg-surface font-mono text-[11px] font-semibold text-accent">
                    {step.n}
                  </span>
                  <div className="flex flex-col gap-1.5 pt-0.5">
                    <span className="text-base font-semibold tracking-tight">{step.title}</span>
                    <p className="max-w-[42ch] text-sm leading-relaxed text-ink-2">{step.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <ThreadPreview />
        </div>
      </div>
    </section>
  );
}

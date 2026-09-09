import { Link } from "react-router-dom";
import { LinkButton } from "../../components/Button";

export function ClosingCta() {
  return (
    <section className="bg-ink text-bg">
      <div className="mx-auto grid w-full max-w-[1240px] grid-cols-1 items-center gap-6 px-4 py-[clamp(38px,5vw,62px)] sm:px-[clamp(18px,5vw,60px)] min-[860px]:grid-cols-[1.2fr_auto]">
        <div className="flex flex-col gap-2.5">
          <h2 className="font-serif text-[clamp(24px,3.2vw,34px)] font-semibold leading-[1.08] tracking-tight text-bg">
            Stop quoting after closing time.
          </h2>
          <p className="max-w-[52ch] text-[15px] leading-relaxed text-[color-mix(in_oklab,var(--bg)_72%,var(--ink))]">
            Connect your WhatsApp number, load your prices once, and let the first reply go out
            while you are still on site.
          </p>
        </div>
        <div className="flex flex-wrap gap-2.5">
          <LinkButton to="/login" variant="primary">
            Start quoting
          </LinkButton>
          <Link
            to="/login"
            className="inline-flex items-center justify-center rounded-lg border border-[color-mix(in_oklab,var(--bg)_34%,var(--ink))] bg-transparent px-5 py-3 text-sm font-medium text-bg transition-colors duration-150 hover:bg-[color-mix(in_oklab,var(--bg)_12%,var(--ink))] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}

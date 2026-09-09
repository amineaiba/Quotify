import { Link } from "react-router-dom";

export function LandingFooter() {
  return (
    <footer className="mx-auto flex w-full max-w-[1240px] flex-wrap items-center gap-3.5 border-t border-line px-4 py-5 sm:px-[clamp(18px,5vw,60px)]">
      <p className="text-sm text-ink-3">
        Used by contractors, repair shops and service providers across Algiers, Oran and
        Constantine.
      </p>
      <Link
        to="/login"
        className="ml-auto rounded text-sm font-semibold text-accent underline transition-colors duration-150 hover:text-accent-deep focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        Sign in
      </Link>
    </footer>
  );
}

import type { Theme } from "../../lib/useTheme";
import { ClosingCta } from "./ClosingCta";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { LandingFooter } from "./LandingFooter";
import { LandingHeader } from "./LandingHeader";

export function Landing({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  return (
    <div className="flex min-h-screen flex-col bg-bg text-ink">
      <LandingHeader theme={theme} onToggleTheme={onToggleTheme} />
      <main className="flex flex-1 flex-col">
        <Hero />
        <HowItWorks />
        <ClosingCta />
      </main>
      <LandingFooter />
    </div>
  );
}

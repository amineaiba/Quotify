import { Link } from "react-router-dom";
import { Button } from "../../components/Button";
import { ThemeToggle } from "../../components/ThemeToggle";
import type { Theme } from "../../lib/useTheme";

export function CatalogHeader({
  theme,
  onToggleTheme,
  onLogout,
}: {
  theme: Theme;
  onToggleTheme: () => void;
  onLogout: () => void;
}) {
  return (
    <header className="sticky top-0 z-10 flex items-center gap-3.5 border-b border-line bg-bg/90 px-4 py-3.5 backdrop-blur-sm sm:px-10">
      <Link
        to="/"
        className="flex items-center gap-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <span className="h-[22px] w-[22px] rounded-[6px_6px_6px_2px] bg-accent" />
        <span className="font-serif text-[19px] font-semibold tracking-tight">Quotify</span>
      </Link>
      <span className="ml-1 text-sm font-medium text-ink-3">Catalog</span>
      <div className="ml-auto flex items-center gap-2">
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        <Button variant="secondary" size="sm" onClick={onLogout}>
          Log out
        </Button>
      </div>
    </header>
  );
}

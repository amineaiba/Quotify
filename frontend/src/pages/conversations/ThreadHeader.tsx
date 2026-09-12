import { Button, LinkButton } from "../../components/Button";
import { ThemeToggle } from "../../components/ThemeToggle";
import type { Client } from "../../lib/conversations";
import type { Theme } from "../../lib/useTheme";

export function ThreadHeader({
  client,
  theme,
  onToggleTheme,
  onLogout,
}: {
  client: Client;
  theme: Theme;
  onToggleTheme: () => void;
  onLogout: () => void;
}) {
  return (
    <header className="sticky top-0 z-10 flex items-center gap-3.5 border-b border-line bg-bg/90 px-4 py-3.5 backdrop-blur-sm sm:px-10">
      <LinkButton to="/inbox" variant="secondary" size="sm">
        Back
      </LinkButton>
      <div className="flex min-w-0 flex-col gap-0.5">
        <span className="truncate text-sm font-semibold">{client.name ?? client.phone_number}</span>
        <span className="truncate font-mono text-xs text-ink-3">
          {client.phone_number} · WhatsApp
        </span>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        <Button variant="secondary" size="sm" onClick={onLogout}>
          Log out
        </Button>
      </div>
    </header>
  );
}

import type { Theme } from "../lib/useTheme";

export function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="flex h-9 w-9 items-center justify-center rounded-full border border-line-strong bg-surface text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      {theme === "dark" ? (
        <svg
          viewBox="0 0 24 24"
          width="17"
          height="17"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="4.2" />
          <path d="M12 3v1.6M12 19.4V21M21 12h-1.6M4.6 12H3M18.4 5.6l-1.1 1.1M6.7 17.3l-1.1 1.1M18.4 18.4l-1.1-1.1M6.7 6.7 5.6 5.6" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
          <path d="M20.4 14.7A8.5 8.5 0 0 1 9.3 3.6a.7.7 0 0 0-.85-.9A9.9 9.9 0 1 0 21.3 15.5a.7.7 0 0 0-.9-.8Z" />
        </svg>
      )}
    </button>
  );
}

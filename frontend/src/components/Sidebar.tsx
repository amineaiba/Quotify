import { Link, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/inbox", label: "Conversations", match: (path: string) => path.startsWith("/inbox") },
  { to: "/review", label: "Review queue", match: (path: string) => path === "/review" },
  { to: "/quotes", label: "Quote history", match: (path: string) => path === "/quotes" },
  { to: "/catalog", label: "Catalog", match: (path: string) => path === "/catalog" },
];

function NavLink({ to, label, active }: { to: string; label: string; active: boolean }) {
  return (
    <Link
      to={to}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ${
        active ? "bg-surface-2 text-ink" : "text-ink-2 hover:bg-surface-2 hover:text-ink"
      }`}
    >
      {label}
    </Link>
  );
}

const Logo = () => (
  <Link
    to="/"
    className="flex items-center gap-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
  >
    <span className="h-[22px] w-[22px] rounded-[6px_6px_6px_2px] bg-accent" />
    <span className="font-serif text-[19px] font-semibold tracking-tight">Quotify</span>
  </Link>
);

/** Dashboard nav — a left column on sm+, a horizontal strip above the page header on mobile. */
export function Sidebar() {
  const { pathname } = useLocation();

  return (
    <>
      <nav className="flex items-center gap-1 border-b border-line bg-bg px-4 py-2.5 sm:hidden">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} label={item.label} active={item.match(pathname)} />
        ))}
      </nav>

      <div className="hidden shrink-0 flex-col gap-6 border-r border-line bg-surface-3 px-3.5 py-5 sm:flex sm:w-56">
        <div className="px-1.5">
          <Logo />
        </div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} label={item.label} active={item.match(pathname)} />
          ))}
        </nav>
      </div>
    </>
  );
}

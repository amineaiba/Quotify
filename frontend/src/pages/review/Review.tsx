import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "../../components/Sidebar";
import { useAuth } from "../../lib/AuthContext";
import { quotesApi } from "../../lib/quotes";
import type { Theme } from "../../lib/useTheme";
import { ReviewHeader } from "./ReviewHeader";
import { ReviewQuoteCard } from "./ReviewQuoteCard";

export function Review({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const quotesQuery = useQuery({
    queryKey: ["quotes", "pending"],
    queryFn: () => quotesApi.list("pending"),
  });

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="bg-bg text-ink sm:flex sm:min-h-screen">
      <Sidebar />

      <div className="min-w-0 flex-1">
        <ReviewHeader theme={theme} onToggleTheme={onToggleTheme} onLogout={handleLogout} />

        <main className="mx-auto flex max-w-2xl flex-col gap-4 px-4 py-8 sm:px-10">
          <div>
            <h1 className="font-serif text-2xl font-semibold tracking-tight">Review queue</h1>
            <p className="text-sm text-ink-2">
              Quotify held these back. Nothing has been sent to the client.
            </p>
          </div>

          {quotesQuery.isLoading && <p className="text-sm text-ink-3">Loading…</p>}
          {quotesQuery.isError && (
            <p className="text-sm text-alert">
              Couldn't load the review queue. Try reloading the page.
            </p>
          )}
          {quotesQuery.data?.length === 0 && (
            <div className="flex flex-col items-center gap-1.5 rounded-[14px] border border-dashed border-line-strong bg-surface px-6 py-14 text-center">
              <span className="text-sm font-medium text-ink-2">Nothing to review</span>
              <span className="text-sm text-ink-3">Held quotes will show up here.</span>
            </div>
          )}
          {quotesQuery.data?.map((quote) => <ReviewQuoteCard key={quote.id} quote={quote} />)}
        </main>
      </div>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sidebar } from "../../components/Sidebar";
import { useAuth } from "../../lib/AuthContext";
import { quotesApi } from "../../lib/quotes";
import type { Theme } from "../../lib/useTheme";
import { QuoteHistoryFilterTabs, type HistoryFilter } from "./QuoteHistoryFilterTabs";
import { QuoteHistoryHeader } from "./QuoteHistoryHeader";
import { QuoteHistoryList } from "./QuoteHistoryList";

export function QuoteHistory({
  theme,
  onToggleTheme,
}: {
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<HistoryFilter>("all");

  const quotesQuery = useQuery({
    queryKey: ["quotes", "history", filter],
    queryFn: () => quotesApi.list(filter === "all" ? undefined : filter),
  });

  // "all" still comes back from one endpoint that includes pending quotes —
  // those belong to the Review queue screen, not history, so drop them here.
  const rows = quotesQuery.data?.filter((quote) => quote.status !== "pending") ?? [];

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="bg-bg text-ink sm:flex sm:min-h-screen">
      <Sidebar />

      <div className="min-w-0 flex-1">
        <QuoteHistoryHeader theme={theme} onToggleTheme={onToggleTheme} onLogout={handleLogout} />

        <main className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-8 sm:px-10">
          <div>
            <h1 className="font-serif text-2xl font-semibold tracking-tight">Quote history</h1>
            <p className="text-sm text-ink-2">Sent, approved, and rejected quotes.</p>
          </div>

          <QuoteHistoryFilterTabs active={filter} onChange={setFilter} />

          {quotesQuery.isLoading && <p className="text-sm text-ink-3">Loading…</p>}
          {quotesQuery.isError && (
            <p className="text-sm text-alert">Couldn't load quote history. Try reloading the page.</p>
          )}
          {quotesQuery.data && <QuoteHistoryList quotes={rows} />}
        </main>
      </div>
    </div>
  );
}

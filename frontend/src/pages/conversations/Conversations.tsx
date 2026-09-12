import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../lib/AuthContext";
import { conversationsApi, type ConversationFilter } from "../../lib/conversations";
import type { Theme } from "../../lib/useTheme";
import { ConversationsFilterTabs } from "./ConversationsFilterTabs";
import { ConversationsHeader } from "./ConversationsHeader";
import { ConversationsList } from "./ConversationsList";

export function Conversations({
  theme,
  onToggleTheme,
}: {
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<ConversationFilter>("all");

  const conversationsQuery = useQuery({
    queryKey: ["conversations", filter],
    queryFn: () => conversationsApi.list(filter),
  });

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-bg text-ink">
      <ConversationsHeader theme={theme} onToggleTheme={onToggleTheme} onLogout={handleLogout} />

      <main className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-8 sm:px-10">
        <div>
          <h1 className="font-serif text-2xl font-semibold tracking-tight">Conversations</h1>
          <p className="text-sm text-ink-2">Client threads on WhatsApp.</p>
        </div>

        <ConversationsFilterTabs active={filter} onChange={setFilter} />

        {conversationsQuery.isLoading && <p className="text-sm text-ink-3">Loading…</p>}
        {conversationsQuery.isError && (
          <p className="text-sm text-alert">Couldn't load conversations. Try reloading the page.</p>
        )}
        {conversationsQuery.data && (
          <ConversationsList conversations={conversationsQuery.data} />
        )}
      </main>
    </div>
  );
}

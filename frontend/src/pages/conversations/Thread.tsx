import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { LinkButton } from "../../components/Button";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { conversationsApi } from "../../lib/conversations";
import type { Theme } from "../../lib/useTheme";
import { ThreadHeader } from "./ThreadHeader";
import { ThreadMessages } from "./ThreadMessages";
import { ThreadQuoteCard } from "./ThreadQuoteCard";

export function Thread({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const { id } = useParams<{ id: string }>();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const threadQuery = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => conversationsApi.get(id!),
    enabled: !!id,
  });

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  if (threadQuery.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <span className="text-sm text-ink-3">Loading…</span>
      </div>
    );
  }

  if (threadQuery.isError) {
    const notFound = threadQuery.error instanceof ApiError && threadQuery.error.status === 404;
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-bg text-center">
        <p className="text-sm text-ink-2">
          {notFound ? "This conversation doesn't exist." : "Couldn't load this conversation."}
        </p>
        <LinkButton to="/inbox" variant="secondary" size="sm">
          Back to inbox
        </LinkButton>
      </div>
    );
  }

  if (!threadQuery.data) return null; // unreachable: covered by isLoading/isError above
  const thread = threadQuery.data;

  return (
    <div className="min-h-screen bg-bg text-ink">
      <ThreadHeader
        client={thread.client}
        theme={theme}
        onToggleTheme={onToggleTheme}
        onLogout={handleLogout}
      />

      <main className="mx-auto flex max-w-2xl flex-col gap-4 px-4 py-8 sm:px-10">
        <ThreadMessages messages={thread.messages} />
        {thread.latest_quote && <ThreadQuoteCard quote={thread.latest_quote} />}
      </main>
    </div>
  );
}

import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

/**
 * Renders children only once the stored refresh token has been checked.
 * Gating on `isAuthenticated` alone would bounce an already-logged-in user
 * to /login on every hard reload, since AuthContext starts unauthenticated
 * while it trades the refresh token for a session in the background.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <span className="text-sm text-ink-3">Loading…</span>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return <>{children}</>;
}

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/Button";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { AUTH_ERROR_MESSAGES } from "../../lib/auth";
import { inputClass } from "../../lib/styles";

export function AuthForm() {
  const [isSignup, setIsSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: () => (isSignup ? register({ name, email, password }) : login(email, password)),
    onSuccess: () => navigate("/catalog"),
  });

  const errorMessage =
    mutation.error instanceof ApiError
      ? (AUTH_ERROR_MESSAGES[mutation.error.detail] ?? mutation.error.detail)
      : null;

  return (
    <div className="flex w-full max-w-[396px] flex-col gap-5 rounded-[14px] border border-line bg-surface p-[clamp(22px,5vw,30px)] shadow-[var(--shadow)]">
      <div className="flex flex-col gap-1.5">
        <h2 className="font-serif text-2xl font-semibold tracking-tight">
          {isSignup ? "Create your account" : "Sign in"}
        </h2>
        <p className="text-sm leading-relaxed text-ink-2">
          {isSignup ? "Two minutes, then connect your WhatsApp number." : "Welcome back to Quotify."}
        </p>
      </div>

      <form
        className="flex flex-col gap-3.5"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        {isSignup && (
          <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink-2">
            Business name
            <input
              type="text"
              required
              placeholder="Ets. Belkacem Carrelage"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
            />
          </label>
        )}
        <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink-2">
          Email
          <input
            type="email"
            required
            placeholder="you@business.dz"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </label>
        <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink-2">
          Password
          <input
            type="password"
            required
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
        </label>

        {errorMessage && <p className="text-[13px] text-alert">{errorMessage}</p>}

        <Button type="submit" variant="primary" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "…" : isSignup ? "Create account" : "Sign in"}
        </Button>
      </form>

      <div className="flex flex-wrap items-baseline justify-between gap-3 border-t border-line pt-3.5 text-[13px] text-ink-3">
        <span>{isSignup ? "Already have an account?" : "New to Quotify?"}</span>
        <button
          type="button"
          onClick={() => setIsSignup(!isSignup)}
          className="rounded font-semibold text-accent underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          {isSignup ? "Sign in" : "Create an account"}
        </button>
      </div>
    </div>
  );
}

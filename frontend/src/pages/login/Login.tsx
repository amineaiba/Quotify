import { Link } from "react-router-dom";
import { AuthForm } from "./AuthForm";

export function Login() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-bg px-5 pb-8 pt-10 text-ink">
      <Link
        to="/"
        className="flex items-center gap-2 rounded p-1.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <span className="h-[22px] w-[22px] rounded-[6px_6px_6px_2px] bg-accent" />
        <span className="font-serif text-lg font-bold tracking-tight">Quotify</span>
      </Link>

      <AuthForm />

      <Link
        to="/"
        className="rounded p-2 text-[13px] font-medium text-ink-3 transition-colors duration-150 hover:text-ink-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        What Quotify does
      </Link>
    </div>
  );
}

import type { ButtonHTMLAttributes } from "react";
import { Link, type LinkProps } from "react-router-dom";

type Variant = "primary" | "secondary";
type Size = "sm" | "md";

const BASE =
  "inline-flex items-center justify-center rounded-lg border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "border-accent bg-accent text-accent-on font-semibold hover:bg-accent-deep hover:border-accent-deep",
  secondary: "border-line-strong bg-transparent font-medium hover:bg-surface-2",
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: "px-3.5 py-2 text-sm",
  md: "px-5 py-3 text-sm",
};

function classes(variant: Variant, size: Size, className: string) {
  return `${BASE} ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`;
}

export function LinkButton({
  to,
  variant = "secondary",
  size = "md",
  className = "",
  ...props
}: { to: string; variant?: Variant; size?: Size } & Omit<LinkProps, "to">) {
  return <Link to={to} className={classes(variant, size, className)} {...props} />;
}

export function Button({
  variant = "secondary",
  size = "md",
  className = "",
  ...props
}: { variant?: Variant; size?: Size } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={classes(variant, size, className)} {...props} />;
}

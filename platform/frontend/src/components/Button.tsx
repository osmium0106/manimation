import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "ghost" | "icon" | "danger";
type ButtonSize = "sm" | "md" | "icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  children?: ReactNode;
}

export function Button({
  variant = "ghost",
  size = "md",
  loading = false,
  icon,
  children,
  className = "",
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  const classes = [
    "ui-btn",
    `ui-btn-${variant}`,
    size === "sm" ? "ui-btn-sm" : "",
    size === "icon" ? "ui-btn-icon-only" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <Loader2 size={14} className="spin" aria-hidden /> : icon}
      {children}
    </button>
  );
}

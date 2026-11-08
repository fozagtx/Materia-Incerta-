import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const variants = {
  default: "border-border bg-muted text-foreground",
  outline: "border-border text-muted-foreground",
  strong: "border-strong/40 bg-strong/10 text-strong",
  moderate: "border-moderate/40 bg-moderate/10 text-moderate",
  weak: "border-weak/40 bg-weak/10 text-weak",
  danger: "border-danger/40 bg-danger/10 text-danger",
  accent: "border-accent/40 bg-accent/10 text-accent",
} as const;

export type BadgeVariant = keyof typeof variants;

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-md border px-1.5 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

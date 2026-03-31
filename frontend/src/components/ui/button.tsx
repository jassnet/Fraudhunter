"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant =
  | "default"
  | "destructive"
  | "outline"
  | "secondary"
  | "ghost"
  | "link";

type ButtonSize = "default" | "sm" | "lg" | "icon";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const baseClasses =
  "inline-flex shrink-0 items-center justify-center rounded-[var(--radius)] border text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-40";

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "border-primary bg-primary text-primary-foreground hover:bg-primary/88 active:bg-primary/80",
  destructive:
    "border-destructive bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/85",
  outline:
    "border-input bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground active:bg-accent/80",
  secondary:
    "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/70",
  ghost:
    "border-transparent bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground active:bg-accent/80",
  link: "border-transparent bg-transparent px-0 text-foreground underline-offset-4 hover:underline focus-visible:ring-offset-0",
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "h-10 px-4",
  sm: "h-8 px-3 text-[13px]",
  lg: "h-11 px-6",
  icon: "h-10 w-10",
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(baseClasses, sizeClasses[size], variantClasses[variant], className)}
      {...props}
    />
  )
);

Button.displayName = "Button";

export { Button };

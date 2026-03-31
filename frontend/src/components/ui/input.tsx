import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  function Input({ className, type, ...props }, ref) {
    return (
      <input
        ref={ref}
        type={type}
        data-slot="input"
        className={cn(
          "h-10 w-full min-w-0 rounded-[var(--radius)] border border-input bg-card px-3 text-sm text-foreground outline-none transition-[color,box-shadow,border-color]",
          "placeholder:text-foreground/52 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/45",
          "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-40",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };

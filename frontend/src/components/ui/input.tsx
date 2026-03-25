import * as React from "react";
import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-10 w-full min-w-0 border border-input bg-card px-3 text-sm text-foreground outline-none transition-colors",
        "placeholder:text-foreground/52 focus-visible:border-white focus-visible:ring-1 focus-visible:ring-white",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-40",
        className
      )}
      {...props}
    />
  );
}

export { Input };

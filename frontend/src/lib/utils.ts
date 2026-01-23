export type ClassValue =
  | string
  | number
  | null
  | undefined
  | boolean
  | ClassValue[]
  | Record<string, boolean | null | undefined>;

function clsx(...inputs: ClassValue[]): string {
  const classes: string[] = [];

  const push = (value: ClassValue) => {
    if (!value) return;
    if (typeof value === "string" || typeof value === "number") {
      classes.push(String(value));
      return;
    }
    if (Array.isArray(value)) {
      value.forEach(push);
      return;
    }
    if (typeof value === "object") {
      Object.entries(value).forEach(([key, val]) => {
        if (val) classes.push(key);
      });
    }
  };

  inputs.forEach(push);
  return classes.join(" ");
}

export function cn(...inputs: ClassValue[]) {
  return clsx(...inputs);
}

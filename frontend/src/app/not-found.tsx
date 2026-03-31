import Link from "next/link";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">ページが見つかりません</h1>
        <p className="text-sm leading-6 text-muted-foreground">
          お探しのページは存在しないか、移動した可能性があります。
        </p>
        <Link
          href="/"
          className={cn(
            "inline-flex h-10 items-center justify-center rounded-[var(--radius)] border border-primary bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors",
            "hover:opacity-90 active:opacity-80",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          )}
        >
          ダッシュボードへ戻る
        </Link>
      </div>
    </div>
  );
}

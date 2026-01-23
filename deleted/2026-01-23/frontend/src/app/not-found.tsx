import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-dvh items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4 rounded-xl border bg-card px-6 py-8 text-center">
        <p className="text-xs font-medium uppercase text-muted-foreground">404</p>
        <h1 className="text-balance text-3xl font-semibold">ページが見つかりませんでした</h1>
        <p className="text-pretty text-sm text-muted-foreground">
          URLが正しいか、左のメニューから目的の画面を選択してください。
        </p>
        <Button asChild>
          <Link href="/">ダッシュボードに戻る</Link>
        </Button>
      </div>
    </div>
  );
}

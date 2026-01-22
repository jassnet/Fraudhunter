import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center space-y-4">
      <h2 className="text-4xl font-bold">404 - Page Not Found</h2>
      <p className="text-muted-foreground">ページが見つかりませんでした。</p>
      <Button asChild>
        <Link href="/">ダッシュボードに戻る</Link>
      </Button>
    </div>
  );
}

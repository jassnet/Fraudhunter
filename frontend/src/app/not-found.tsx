import Link from "next/link";

export default function NotFound() {
  return (
    <div className="screen-page">
      <div className="empty-state">
        指定されたページは見つかりません。
        <div className="page-actions-spacer">
          <Link className="top-link" href="/dashboard">
            ダッシュボードへ戻る
          </Link>
        </div>
      </div>
    </div>
  );
}

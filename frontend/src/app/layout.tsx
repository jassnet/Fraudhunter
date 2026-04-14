import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppFrame } from "@/components/app-frame";
import { getConsoleViewer } from "@/lib/server/console-auth";

import "./globals.css";

export const metadata: Metadata = {
  title: "フロードチェッカー",
  description: "アフィリエイト不正検知システムの管理画面",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  await getConsoleViewer();
  return (
    <html lang="ja">
      <body suppressHydrationWarning>
        <AppFrame>{children}</AppFrame>
      </body>
    </html>
  );
}

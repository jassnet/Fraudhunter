import type { Metadata } from "next";
import "./globals.css";
import { MainNav } from "@/components/main-nav";
import { MobileNav } from "@/components/mobile-nav";

export const metadata: Metadata = {
  title: "Fraud Checker v2",
  description: "Fraud detection dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:shadow"
        >
          Skip to content
        </a>
        <div className="flex h-dvh overflow-auto bg-background">
          <aside className="hidden w-64 overflow-y-auto border-r bg-muted/40 md:block">
            <div className="flex h-full flex-col gap-2">
              <div className="flex h-14 items-center border-b px-6 font-semibold lg:h-[60px]">
                <span>Fraud Checker v2</span>
              </div>
              <div className="flex-1 px-4 py-4">
                <MainNav />
              </div>
              <div className="mt-auto border-t p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">v2.0.0</span>
                </div>
              </div>
            </div>
          </aside>

          <div className="flex flex-1 flex-col">
            <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 md:hidden">
              <MobileNav />
              <span className="font-semibold">Fraud Checker v2</span>
            </header>

            <main id="main-content" className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

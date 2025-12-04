import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { MainNav } from "@/components/main-nav";
import { ModeToggle } from "@/components/mode-toggle";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fraud Checker v2",
  description: "Advanced Fraud Detection System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex h-screen overflow-hidden bg-background">
            <aside className="hidden w-64 overflow-y-auto border-r bg-muted/40 md:block">
              <div className="flex h-full flex-col gap-2">
                <div className="flex h-14 items-center border-b px-6 font-semibold lg:h-[60px]">
                  <span className="">Fraud Checker v2</span>
                </div>
                <div className="flex-1 px-4 py-4">
                  <MainNav />
                </div>
                <div className="mt-auto p-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">v2.0.0</span>
                    <ModeToggle />
                  </div>
                </div>
              </div>
            </aside>
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}

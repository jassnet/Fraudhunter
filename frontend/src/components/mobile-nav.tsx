"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  MousePointerClick,
  Target,
  Settings,
  Menu,
} from "lucide-react";

const items = [
  {
    title: "ダッシュボード",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "不正クリック検知",
    href: "/suspicious/clicks",
    icon: MousePointerClick,
  },
  {
    title: "不正成果検知",
    href: "/suspicious/conversions",
    icon: Target,
  },
  {
    title: "設定",
    href: "/settings",
    icon: Settings,
  },
];

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">メニューを開く</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[280px] sm:w-[320px]">
        <SheetHeader>
          <SheetTitle>Fraud Checker v2</SheetTitle>
        </SheetHeader>
        <nav className="mt-8 grid gap-2">
          {items.map((item, index) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={index}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-all",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-primary"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.title}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-4 right-4">
          <p className="text-xs text-muted-foreground">v2.0.0</p>
        </div>
      </SheetContent>
    </Sheet>
  );
}


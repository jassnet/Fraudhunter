export const APP_TITLE = "Fraud Checker";
export const READ_ONLY_LABEL = "閲覧専用";
export const READ_ONLY_LABEL_COMPACT = "閲覧専用";

export const NAV_ITEMS = [
  { title: "ダッシュボード", shortTitle: "Home", href: "/" },
  { title: "不正判定", shortTitle: "Fraud", href: "/suspicious/fraud" },
] as const;

export function getPageTitle(pathname: string | null | undefined) {
  if (!pathname) return APP_TITLE;
  if (pathname.startsWith("/suspicious/fraud") || pathname.startsWith("/suspicious/conversions")) {
    return "不正判定";
  }
  return "ダッシュボード";
}

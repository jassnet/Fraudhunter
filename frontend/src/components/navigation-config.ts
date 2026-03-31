export const APP_TITLE = "Fraud Checker";
export const READ_ONLY_LABEL = "参照専用（書き込みなし）";
export const READ_ONLY_LABEL_COMPACT = "参照専用";

export const NAV_ITEMS = [
  { title: "ダッシュボード", shortTitle: "ダ", href: "/" },
  { title: "不審コンバージョン", shortTitle: "CV", href: "/suspicious/conversions" },
] as const;

export function getPageTitle(pathname: string | null | undefined) {
  if (!pathname) return APP_TITLE;
  if (pathname.startsWith("/suspicious/conversions")) {
    return "不審コンバージョン";
  }
  return "ダッシュボード";
}

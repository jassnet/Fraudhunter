import type { SuspiciousItem, SuspiciousRiskLevel } from "@/lib/api";

export function getReasonClusterKey(item: SuspiciousItem): string {
  const key = item.reason_cluster_key?.trim();
  if (key) return key;
  const groups = item.reason_groups;
  if (groups && groups.length > 0) {
    return groups.join("\u0001");
  }
  const raw = item.reasons ?? [];
  if (raw.length === 0) return "";
  return `raw:${[...raw].sort().join("\n")}`;
}

export interface SuspiciousClusterGroup {
  clusterKey: string;
  members: SuspiciousItem[];
}

export function clusterSuspiciousItems(data: SuspiciousItem[]): SuspiciousClusterGroup[] {
  const order: string[] = [];
  const map = new Map<string, SuspiciousItem[]>();
  for (const item of data) {
    const k = getReasonClusterKey(item);
    if (!map.has(k)) {
      map.set(k, []);
      order.push(k);
    }
    map.get(k)!.push(item);
  }
  return order.map((clusterKey) => ({
    clusterKey,
    members: map.get(clusterKey)!,
  }));
}

const RISK_WEIGHT: Record<SuspiciousRiskLevel, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

export function worstRiskLevel(items: SuspiciousItem[]): SuspiciousRiskLevel | undefined {
  let best: SuspiciousRiskLevel | undefined;
  let bestW = 0;
  for (const it of items) {
    const lvl = it.risk_level;
    if (!lvl) continue;
    const w = RISK_WEIGHT[lvl] ?? 0;
    if (w > bestW) {
      bestW = w;
      best = lvl;
    }
  }
  return best;
}

export function worstRiskLabel(items: SuspiciousItem[]): string | undefined {
  const lvl = worstRiskLevel(items);
  if (!lvl) return undefined;
  const withLevel = items.find((it) => it.risk_level === lvl);
  return withLevel?.risk_label ?? lvl;
}

export function sumConversions(items: SuspiciousItem[]): number {
  return items.reduce((acc, it) => {
    const value = it.total_conversions;
    return acc + (typeof value === "number" ? value : 0);
  }, 0);
}

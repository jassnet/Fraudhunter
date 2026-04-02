from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


@dataclass
class FraudThresholds:
    check_min_total: int
    check_invalid_rate: int
    check_duplicate_plid_count: int
    check_duplicate_plid_rate: int
    track_min_total: int
    track_auth_error_rate: int
    track_auth_ip_ua_rate: int
    action_min_total: int
    action_short_gap_seconds: int
    action_short_gap_count: int
    action_cancel_rate: int
    action_fixed_gap_min_count: int
    action_fixed_gap_max_unique: int
    spike_multiplier: int
    spike_lookback_days: int


@dataclass
class EntityState:
    conversions: list[dict[str, Any]] = field(default_factory=list)
    tracks: list[dict[str, Any]] = field(default_factory=list)
    click_count: int = 0
    access_count: int = 0
    imp_count: int = 0


class AcsNativeFraudDetector:
    def __init__(self, repo, settings: dict):
        self.repo = repo
        self.thresholds = FraudThresholds(
            check_min_total=settings["fraud_check_min_total"],
            check_invalid_rate=settings["fraud_check_invalid_rate"],
            check_duplicate_plid_count=settings["fraud_check_duplicate_plid_count"],
            check_duplicate_plid_rate=settings["fraud_check_duplicate_plid_rate"],
            track_min_total=settings["fraud_track_min_total"],
            track_auth_error_rate=settings["fraud_track_auth_error_rate"],
            track_auth_ip_ua_rate=settings["fraud_track_auth_ip_ua_rate"],
            action_min_total=settings["fraud_action_min_total"],
            action_short_gap_seconds=settings["fraud_action_short_gap_seconds"],
            action_short_gap_count=settings["fraud_action_short_gap_count"],
            action_cancel_rate=settings["fraud_action_cancel_rate"],
            action_fixed_gap_min_count=settings["fraud_action_fixed_gap_min_count"],
            action_fixed_gap_max_unique=settings["fraud_action_fixed_gap_max_unique"],
            spike_multiplier=settings["fraud_spike_multiplier"],
            spike_lookback_days=settings["fraud_spike_lookback_days"],
        )

    def find_for_date(self, target_date: date) -> list[dict[str, Any]]:
        metric_rows = self.repo.list_fraud_metric_rows(target_date)
        entity_map: dict[tuple[str, str, str], EntityState] = defaultdict(EntityState)
        action_to_entity: dict[str, tuple[str, str, str]] = {}

        for conversion in metric_rows["conversions"]:
            if not conversion.get("user_id") or not conversion.get("media_id") or not conversion.get("program_id"):
                continue
            key = (
                str(conversion["user_id"]),
                str(conversion["media_id"]),
                str(conversion["program_id"]),
            )
            entity_map[key].conversions.append(conversion)
            action_to_entity[str(conversion["id"])] = key

        for metric_key, field_name in (
            ("click_metrics", "click_count"),
            ("access_metrics", "access_count"),
            ("imp_metrics", "imp_count"),
        ):
            for row in metric_rows[metric_key]:
                key = (str(row["user_id"]), str(row["media_id"]), str(row["promotion_id"]))
                setattr(entity_map[key], field_name, int(row["metric_value"] or 0))

        for track in metric_rows["tracks"]:
            action_id = track.get("action_log_raw_id")
            if not action_id or action_id not in action_to_entity:
                continue
            entity_map[action_to_entity[action_id]].tracks.append(track)

        check_by_user = self._build_check_metrics(metric_rows["checks"])
        historical_metrics = self._load_historical_metrics(target_date)

        findings: list[dict[str, Any]] = []
        for entity_key, state in entity_map.items():
            user_id, media_id, promotion_id = entity_key
            reasons: list[str] = []
            metrics = self._build_entity_metrics(
                target_date,
                entity_key,
                state,
                check_by_user.get(user_id),
                historical_metrics,
                reasons,
            )
            if not reasons:
                continue
            names = self._lookup_names(user_id, media_id, promotion_id)
            findings.append(
                {
                    "date": target_date,
                    "user_id": user_id,
                    "media_id": media_id,
                    "promotion_id": promotion_id,
                    "user_name": names["user_name"],
                    "media_name": names["media_name"],
                    "promotion_name": names["promotion_name"],
                    "primary_metric": metrics["action_total"] or metrics["click_count"] or metrics["check_total"],
                    "reasons": reasons,
                    "metrics": metrics,
                    "first_event_time": metrics.get("first_time"),
                    "last_event_time": metrics.get("last_time"),
                }
            )
        return findings

    def _build_check_metrics(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if row.get("affiliate_user_id"):
                by_user[str(row["affiliate_user_id"])].append(row)
        metrics: dict[str, dict[str, Any]] = {}
        for user_id, checks in by_user.items():
            total = len(checks)
            invalid_count = sum(1 for row in checks if int(row.get("state") or -1) == 0)
            plids = [str(row["plid"]) for row in checks if row.get("plid")]
            duplicates = sum(count for count in Counter(plids).values() if count > 1)
            metrics[user_id] = {
                "check_total": total,
                "check_invalid_count": invalid_count,
                "check_invalid_rate": (invalid_count / total) if total else 0,
                "check_duplicate_plid_count": duplicates,
                "check_duplicate_plid_rate": (duplicates / total) if total else 0,
            }
        return metrics

    def _build_entity_metrics(
        self,
        target_date: date,
        entity_key: tuple[str, str, str],
        state: EntityState,
        check_metrics: dict[str, Any] | None,
        historical_metrics: dict[str, dict[tuple[str, str, str], list[int]]],
        reasons: list[str],
    ) -> dict[str, Any]:
        conversions = state.conversions
        tracks = state.tracks
        action_total = len(conversions)
        cancel_count = sum(1 for row in conversions if str(row.get("state")) == "2")
        gaps = [
            max(0, int((row["conversion_time"] - row["click_time"]).total_seconds()))
            for row in conversions
            if row.get("click_time") and row.get("conversion_time")
        ]
        short_gap_count = sum(1 for value in gaps if value <= self.thresholds.action_short_gap_seconds)
        unique_gap_count = len(set(gaps)) if gaps else 0
        track_total = len(tracks)
        auth_error_count = sum(1 for row in tracks if row.get("auth_type") == "error")
        auth_ip_ua_count = sum(1 for row in tracks if row.get("auth_type") == "ip_ua")
        first_time = min((row["conversion_time"] for row in conversions), default=None)
        last_time = max((row["conversion_time"] for row in conversions), default=None)
        metrics = {
            **(check_metrics or {
                "check_total": 0,
                "check_invalid_count": 0,
                "check_invalid_rate": 0,
                "check_duplicate_plid_count": 0,
                "check_duplicate_plid_rate": 0,
            }),
            "track_total": track_total,
            "track_auth_error_count": auth_error_count,
            "track_auth_error_rate": (auth_error_count / track_total) if track_total else 0,
            "track_auth_ip_ua_count": auth_ip_ua_count,
            "track_auth_ip_ua_rate": (auth_ip_ua_count / track_total) if track_total else 0,
            "action_total": action_total,
            "action_cancel_count": cancel_count,
            "action_cancel_rate": (cancel_count / action_total) if action_total else 0,
            "action_short_gap_count": short_gap_count,
            "action_fixed_gap_unique_count": unique_gap_count,
            "min_click_to_conv_seconds": min(gaps) if gaps else None,
            "max_click_to_conv_seconds": max(gaps) if gaps else None,
            "click_count": state.click_count,
            "access_count": state.access_count,
            "imp_count": state.imp_count,
            "ctr": (state.click_count / state.imp_count) if state.imp_count else None,
            "first_time": first_time,
            "last_time": last_time,
        }
        if metrics["check_total"] >= self.thresholds.check_min_total:
            if metrics["check_invalid_rate"] * 100 >= self.thresholds.check_invalid_rate:
                reasons.append("check_invalid_rate")
            if (
                metrics["check_duplicate_plid_count"] >= self.thresholds.check_duplicate_plid_count
                or metrics["check_duplicate_plid_rate"] * 100 >= self.thresholds.check_duplicate_plid_rate
            ):
                reasons.append("check_duplicate_plid")
        if track_total >= self.thresholds.track_min_total:
            if metrics["track_auth_error_rate"] * 100 >= self.thresholds.track_auth_error_rate:
                reasons.append("track_auth_error_rate")
            if metrics["track_auth_ip_ua_rate"] * 100 >= self.thresholds.track_auth_ip_ua_rate:
                reasons.append("track_auth_ip_ua_rate")
        if action_total >= self.thresholds.action_min_total:
            if short_gap_count >= self.thresholds.action_short_gap_count:
                reasons.append("action_short_gap")
            if (
                len(gaps) >= self.thresholds.action_fixed_gap_min_count
                and unique_gap_count <= self.thresholds.action_fixed_gap_max_unique
            ):
                reasons.append("action_fixed_gap_pattern")
            if metrics["action_cancel_rate"] * 100 >= self.thresholds.action_cancel_rate:
                reasons.append("action_cancel_rate")
        if self._has_duplicate_guard(promotion_id=entity_key[2]) and (
            "action_short_gap" in reasons
            or "action_fixed_gap_pattern" in reasons
            or "check_duplicate_plid" in reasons
        ):
            reasons.append("promotion_duplicate_guard_bypass_risk")
        for reason_name, metric_name in (
            ("click_spike", "click_count"),
            ("access_spike", "access_count"),
            ("ctr_spike", "ctr"),
        ):
            baseline = self._baseline_for(historical_metrics[metric_name].get(entity_key, []))
            value = metrics[metric_name]
            if baseline is None or value is None:
                continue
            if value >= baseline * self.thresholds.spike_multiplier:
                reasons.append(reason_name)
        return metrics

    def _load_historical_metrics(self, target_date: date) -> dict[str, dict[tuple[str, str, str], list[int]]]:
        start_date = target_date - timedelta(days=self.thresholds.spike_lookback_days)
        historical = {
            "click_count": defaultdict(list),
            "access_count": defaultdict(list),
            "ctr": defaultdict(list),
        }
        for table_name, metric_name in (
            ("click_sum_daily", "click_count"),
            ("access_sum_daily", "access_count"),
            ("imp_sum_daily", "imp_count"),
        ):
            rows = self.repo.fetch_all(
                f"""
                SELECT date, user_id, media_id, promotion_id, {metric_name} AS metric_value
                FROM {table_name}
                WHERE date >= :start_date
                  AND date < :target_date
                """,
                {"start_date": start_date, "target_date": target_date},
            ) if self.repo._table_exists(table_name) else []
            for row in rows:
                key = (str(row["user_id"]), str(row["media_id"]), str(row["promotion_id"]))
                if table_name == "click_sum_daily":
                    historical["click_count"][key].append(int(row["metric_value"] or 0))
                elif table_name == "access_sum_daily":
                    historical["access_count"][key].append(int(row["metric_value"] or 0))
                else:
                    historical.setdefault("_imp", defaultdict(list))[key].append(int(row["metric_value"] or 0))
        imp_history = historical.pop("_imp", defaultdict(list))
        for key, click_values in historical["click_count"].items():
            imp_values = imp_history.get(key, [])
            ctr_values = []
            for idx, click_value in enumerate(click_values):
                imp_value = imp_values[idx] if idx < len(imp_values) else 0
                if imp_value:
                    ctr_values.append(click_value / imp_value)
            if ctr_values:
                historical["ctr"][key].extend(ctr_values)
        return historical

    @staticmethod
    def _baseline_for(values: list[int | float]) -> float | None:
        cleaned = [float(value) for value in values if value is not None]
        if len(cleaned) < 3:
            return None
        return statistics.median(cleaned)

    def _has_duplicate_guard(self, promotion_id: str) -> bool:
        row = self.repo.fetch_one(
            """
            SELECT action_double_state
            FROM master_promotion
            WHERE id = :promotion_id
            """,
            {"promotion_id": promotion_id},
        )
        return bool(row and int(row.get("action_double_state") or 0) == 1)

    def _lookup_names(self, user_id: str, media_id: str, promotion_id: str) -> dict[str, Any]:
        user_row = self.repo.fetch_one("SELECT name FROM master_user WHERE id = :id", {"id": user_id})
        media_row = self.repo.fetch_one("SELECT name FROM master_media WHERE id = :id", {"id": media_id})
        promo_row = self.repo.fetch_one("SELECT name FROM master_promotion WHERE id = :id", {"id": promotion_id})
        return {
            "user_name": user_row.get("name") if user_row else None,
            "media_name": media_row.get("name") if media_row else None,
            "promotion_name": promo_row.get("name") if promo_row else None,
        }

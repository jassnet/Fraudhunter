from __future__ import annotations

from datetime import date, datetime, timedelta

from fraud_checker.api_presenters import (
    build_reason_display,
    calculate_risk_level,
    present_conversion_finding_record,
)


SPREAD_BOTH = "\u540c\u4e00 IP/UA \u3067\u8907\u6570\u5a92\u4f53\u30fb\u8907\u6570\u6848\u4ef6\u306b\u307e\u305f\u304c\u308b\u6210\u679c\u304c\u3042\u308a\u307e\u3059"
SPREAD_PROGRAM = "\u540c\u4e00 IP/UA \u3067\u8907\u6570\u6848\u4ef6\u306b\u307e\u305f\u304c\u308b\u6210\u679c\u304c\u3042\u308a\u307e\u3059"
BURST_CONVERSION = "\u77ed\u6642\u9593\u306b\u6210\u679c\u304c\u96c6\u4e2d\u3057\u3066\u3044\u307e\u3059"
CLICK_PADDING = "\u4e0d\u5be9CV\u3092\u96a0\u3059\u305f\u3081\u306e\u30af\u30ea\u30c3\u30af\u4e0a\u4e57\u305b\u304c\u7591\u308f\u308c\u307e\u3059"


def test_build_reason_display_groups_media_and_program_into_single_reason():
    payload = build_reason_display(
        ["media_count >= 2", "program_count >= 2"],
        is_conversion=True,
    )

    assert payload["reason_groups"] == [SPREAD_BOTH]
    assert payload["reason_group_count"] == 1
    assert payload["reason_summary"] == SPREAD_BOTH
    assert payload["reason_cluster_key"] == "spread_both"


def test_build_reason_display_prioritizes_spread_reason_over_burst():
    payload = build_reason_display(
        ["program_count >= 2", "burst: 3 conversions in 0s (<= 1800s)"],
        is_conversion=True,
    )

    assert payload["reason_group_count"] == 2
    assert payload["reason_groups"] == [SPREAD_PROGRAM, BURST_CONVERSION]
    assert payload["reason_cluster_key"] == "burst|spread_program"


def test_present_conversion_finding_record_keeps_risk_and_adds_grouped_fields():
    first_time = datetime(2026, 1, 1, 10, 0, 0)
    row = {
        "finding_key": "finding-1",
        "date": date(2026, 1, 1),
        "ipaddress": "1.1.1.1",
        "useragent": "Mozilla/5.0",
        "total_conversions": 3,
        "media_count": 1,
        "program_count": 2,
        "first_time": first_time,
        "last_time": first_time + timedelta(seconds=10),
        "reasons_json": ["program_count >= 2", "burst: 3 conversions in 0s (<= 1800s)"],
        "reasons_formatted_json": ["legacy spread", "legacy burst"],
        "min_click_to_conv_seconds": 12,
        "max_click_to_conv_seconds": 30,
        "risk_level": "high",
        "risk_score": 85,
        "metrics_json": {},
        "media_names_json": ["Media 1"],
        "program_names_json": ["Program 1"],
        "affiliate_names_json": ["Affiliate 1"],
    }

    payload = present_conversion_finding_record(row, mask_sensitive=False)

    assert payload["risk_level"] == "high"
    assert payload["risk_score"] == 85
    assert payload["reason_summary"] == SPREAD_PROGRAM
    assert payload["reason_group_count"] == 2
    assert payload["reason_groups"] == [SPREAD_PROGRAM, BURST_CONVERSION]
    assert payload["reason_cluster_key"] == "burst|spread_program"


def test_build_reason_display_prioritizes_click_padding_over_burst():
    payload = build_reason_display(
        [
            "click_padding_linked_ratio >= 2.0 (actual=3.00)",
            "burst: 3 conversions in 0s (<= 1800s)",
        ],
        is_conversion=True,
    )

    assert payload["reason_summary"] == CLICK_PADDING
    assert payload["reason_groups"] == [CLICK_PADDING, BURST_CONVERSION]
    assert payload["reason_cluster_key"] == "burst|click_padding"


def test_present_conversion_finding_record_reads_padding_metrics_from_metrics_json():
    first_time = datetime(2026, 1, 1, 10, 0, 0)
    row = {
        "finding_key": "finding-2",
        "date": date(2026, 1, 1),
        "ipaddress": "2.2.2.2",
        "useragent": "Mozilla/5.0",
        "total_conversions": 5,
        "media_count": 1,
        "program_count": 1,
        "first_time": first_time,
        "last_time": first_time + timedelta(seconds=10),
        "reasons_json": ["click_padding_linked_ratio >= 2.0 (actual=3.20)"],
        "reasons_formatted_json": ["formatted padding"],
        "min_click_to_conv_seconds": None,
        "max_click_to_conv_seconds": None,
        "risk_level": "high",
        "risk_score": 125,
        "metrics_json": {
            "linked_click_count": 16,
            "linked_clicks_per_conversion": 3.2,
            "extra_window_click_count": 12,
            "extra_window_non_browser_ratio": 0.75,
        },
        "media_names_json": [],
        "program_names_json": [],
        "affiliate_names_json": [],
    }

    payload = present_conversion_finding_record(row, mask_sensitive=False)

    assert payload["linked_click_count"] == 16
    assert payload["linked_clicks_per_conversion"] == 3.2
    assert payload["extra_window_click_count"] == 12
    assert payload["extra_window_non_browser_ratio"] == 0.75
    assert payload["reason_cluster_key"] == "click_padding"


def test_calculate_risk_level_adds_click_padding_bonus_once():
    risk = calculate_risk_level(
        [
            "conversion_count >= 5",
            "click_padding_linked_ratio >= 2.0 (actual=3.00)",
            "click_padding_extra_window >= 10 in 30m (actual=12)",
        ],
        count=5,
        is_conversion=True,
    )

    assert risk == {"level": "high", "score": 105, "label": "高リスク"}

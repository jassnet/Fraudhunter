from fraud_checker.services import settings as settings_service
from fraud_checker.suspicious import ConversionSuspiciousRuleSet, SuspiciousRuleSet


def test_build_rule_sets_uses_settings(monkeypatch):
    fake_settings = {
        "click_threshold": 11,
        "media_threshold": 2,
        "program_threshold": 3,
        "burst_click_threshold": 4,
        "burst_window_seconds": 500,
        "conversion_threshold": 6,
        "conv_media_threshold": 7,
        "conv_program_threshold": 8,
        "burst_conversion_threshold": 9,
        "burst_conversion_window_seconds": 700,
        "min_click_to_conv_seconds": 10,
        "max_click_to_conv_seconds": 999,
        "browser_only": True,
        "exclude_datacenter_ip": True,
    }

    monkeypatch.setattr(settings_service, "get_settings", lambda repo: fake_settings)

    click_rules, conversion_rules = settings_service.build_rule_sets(repo=None)  # type: ignore[arg-type]

    assert isinstance(click_rules, SuspiciousRuleSet)
    assert isinstance(conversion_rules, ConversionSuspiciousRuleSet)
    assert click_rules.click_threshold == 11
    assert click_rules.burst_window_seconds == 500
    assert click_rules.browser_only is True
    assert conversion_rules.conversion_threshold == 6
    assert conversion_rules.burst_conversion_threshold == 9
    assert conversion_rules.max_click_to_conv_seconds == 999

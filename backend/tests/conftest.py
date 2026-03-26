from __future__ import annotations


# The old Japanese display-name map was partially mojibake and made pytest output
# harder to trust than the original test names. Keep the hook in place so we can
# restore curated labels later without changing pytest configuration again.
JP_TEST_NAME_MAP: dict[str, str] = {}


def pytest_collection_modifyitems(items):
    for item in items:
        original_name = getattr(item, "originalname", item.name)
        jp_name = JP_TEST_NAME_MAP.get(original_name)
        if not jp_name:
            continue
        item.name = jp_name
        base_nodeid = item.nodeid.rsplit("::", 1)[0]
        item._nodeid = f"{base_nodeid}::{jp_name}"

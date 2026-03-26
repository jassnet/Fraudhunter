from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UTF8_TARGETS = (
    ROOT / ".editorconfig",
    ROOT / ".gitattributes",
    ROOT / "backend" / "src",
    ROOT / "backend" / "tests",
    ROOT / "frontend" / "src",
    ROOT / "docs",
)


def _iter_files():
    for target in UTF8_TARGETS:
        if target.is_file():
            yield target
            continue
        for path in target.rglob("*"):
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".css", ".md", ".json", ".yml", ".yaml"}:
                continue
            yield path


def test_utf8_targets_are_valid_utf8_without_bom_or_replacement_chars() -> None:
    for path in _iter_files():
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} has a UTF-8 BOM"
        decoded = raw.decode("utf-8")
        assert "\ufffd" not in decoded, f"{path} contains replacement characters"


def test_job_queue_messages_are_not_mojibake() -> None:
    jobs_source = (ROOT / "backend" / "src" / "fraud_checker" / "services" / "jobs.py").read_text(
        encoding="utf-8"
    )

    assert "\\u30de\\u30b9\\u30bf\\u540c\\u671f\\u30b8\\u30e7\\u30d6" in jobs_source
    assert "\\u76f4\\u8fd1{hours}\\u6642\\u9593\\u306e\\u518d\\u53d6\\u5f97\\u30b8\\u30e7\\u30d6" in jobs_source

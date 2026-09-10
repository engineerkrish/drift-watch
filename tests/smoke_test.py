from pathlib import Path

from driftwatch.scanner.code_scanner import scan_code
from driftwatch.scanner.config_scanner import scan_configs
from driftwatch.engine.drift_engine import build_findings


def scan_fixture(root: Path):
    used = scan_code(root)
    configs = scan_configs(root)
    return build_findings(used, configs)


def test_demo_detects_drift():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "demo"

    findings = scan_fixture(root)

    categories = {finding.category for finding in findings}

    assert "missing" in categories
    assert "orphaned" in categories


def test_type_mismatch_detection(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    (source_dir / "app.py").write_text(
        'import os\n'
        'retry_count = os.getenv("MAX_RETRY_COUNT")\n',
        encoding="utf-8",
    )

    (tmp_path / ".env.development").write_text(
        "MAX_RETRY_COUNT=5\n",
        encoding="utf-8",
    )

    (tmp_path / ".env.staging").write_text(
        "MAX_RETRY_COUNT=5\n",
        encoding="utf-8",
    )

    (tmp_path / ".env.production").write_text(
        'MAX_RETRY_COUNT="5"\n',
        encoding="utf-8",
    )

    findings = scan_fixture(tmp_path)

    mismatches = [
        finding
        for finding in findings
        if finding.category == "type-mismatch"
        and finding.key == "MAX_RETRY_COUNT"
    ]

    assert len(mismatches) == 1
    assert "production=string" in mismatches[0].note


def test_secret_values_never_appear():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "demo"

    findings = scan_fixture(root)

    forbidden = [
        "dev-secret-never-printed",
        "staging-secret-never-printed",
        "prod-secret-never-printed",
        "FAKE_SECRET_VALUE",
        "fake-password",
    ]

    rendered = repr(findings)

    for secret in forbidden:
        assert secret not in rendered


def test_scan_is_repeatable():
    root = Path(__file__).resolve().parents[1] / "fixtures" / "demo"

    first = scan_fixture(root)
    second = scan_fixture(root)

    first_fingerprints = sorted(f.fingerprint for f in first)
    second_fingerprints = sorted(f.fingerprint for f in second)

    assert first_fingerprints == second_fingerprints
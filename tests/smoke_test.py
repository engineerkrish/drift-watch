from driftwatch.scanner.code_scanner import scan_code
from driftwatch.scanner.config_scanner import scan_configs
from driftwatch.engine.drift_engine import build_findings


def test_driftwatch_detects_core_drift(tmp_path):
    # Create a completely isolated test repository.
    root = tmp_path

    src = root / "src"
    src.mkdir()

    # Code references:
    # - DATABASE_URL -> defined everywhere
    # - PAYMENTS_WEBHOOK_SECRET -> missing in staging
    # - MAX_RETRY_COUNT -> type mismatch in production
    code = src / "app.py"
    code.write_text(
        """
import os

database_url = os.getenv("DATABASE_URL")
webhook_secret = os.getenv("PAYMENTS_WEBHOOK_SECRET")
max_retry_count = os.getenv("MAX_RETRY_COUNT")
""",
        encoding="utf-8",
    )

    # Development: numeric 5
    (root / ".env.development").write_text(
        """
DATABASE_URL=postgres://dev
PAYMENTS_WEBHOOK_SECRET=dev-secret
MAX_RETRY_COUNT=5
ORPHAN_KEY=hello
""",
        encoding="utf-8",
    )

    # Staging: missing PAYMENTS_WEBHOOK_SECRET
    (root / ".env.staging").write_text(
        """
DATABASE_URL=postgres://staging
MAX_RETRY_COUNT=5
ORPHAN_KEY=hello
""",
        encoding="utf-8",
    )

    # Production: quoted "5" -> string, creating type mismatch
    (root / ".env.production").write_text(
        """
DATABASE_URL=postgres://production
PAYMENTS_WEBHOOK_SECRET=prod-secret
MAX_RETRY_COUNT="5"
ORPHAN_KEY=hello
""",
        encoding="utf-8",
    )

    used = scan_code(root)
    configs = scan_configs(root)
    findings = build_findings(used, configs)

    categories = {finding.category for finding in findings}

    # Core challenge requirements.
    assert "missing" in categories
    assert "orphaned" in categories
    assert "type-mismatch" in categories

    # Make sure the secret value never appears in findings.
    text = str(findings)

    assert "dev-secret" not in text
    assert "prod-secret" not in text

    # Verify the actual keys were detected.
    keys = {finding.key for finding in findings}

    assert "PAYMENTS_WEBHOOK_SECRET" in keys
    assert "MAX_RETRY_COUNT" in keys
    assert "ORPHAN_KEY" in keys
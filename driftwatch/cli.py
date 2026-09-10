import argparse
import sys
from pathlib import Path

from .scanner.code_scanner import scan_code
from .scanner.config_scanner import scan_configs
from .engine.drift_engine import build_findings
from .engine.state import load_state, save_state
from .reporter.terminal import render_terminal
from .reporter.markdown import render_markdown


def main():
    p = argparse.ArgumentParser(
        prog="driftwatch",
        description="Detect configuration drift without exposing secret values.",
    )

    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="scan a repository")
    s.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="repository path",
    )
    s.add_argument(
        "--report",
        default="DRIFT-REPORT.md",
        help="markdown output path",
    )
    s.add_argument(
        "--state",
        default=".driftwatch/state.json",
        help="state file path",
    )

    args = p.parse_args()

    repo = Path(args.repo).resolve()

    if not repo.exists():
        p.error(f"Repository does not exist: {repo}")

    # Scan source code and configuration.
    used = scan_code(repo)
    configs = scan_configs(repo)

    # Build drift findings.
    findings = build_findings(used, configs)

    # Load previous state.
    state_path = repo / args.state
    previous = load_state(state_path)

    current = {f.fingerprint for f in findings}

    new_fps = current - previous
    resolved = previous - current
    still = current & previous

    # Generate Markdown report.
    report_path = repo / args.report

    render_markdown(
        report_path,
        findings,
        new_fps,
        previous,
        resolved,
        repo.name,
    )

    # Persist current fingerprints.
    save_state(state_path, current)

    # Render terminal output.
    render_terminal(
        findings,
        len(new_fps),
        len(still),
        len(resolved),
        repo.name,
    )

    print(f"Report: {report_path.relative_to(repo)}")

    # CI quality gate:
    # Critical findings cause a non-zero exit code.
    # Warning and info findings do not fail the build.
    has_critical = any(
        finding.severity == "critical"
        for finding in findings
    )

    if has_critical:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
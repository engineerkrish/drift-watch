from pathlib import Path
import re
from ..models import CodeUse

# Direct, deterministic patterns. We intentionally do not inspect assigned values.
PATTERNS = [
    ("python", re.compile(r'\bos\.(?:environ\.get|getenv)\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']')),
    ("python", re.compile(r'\bos\.environ\s*\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']')),
    ("js", re.compile(r'\bprocess\.env\.([A-Za-z_][A-Za-z0-9_]*)')),
    ("js", re.compile(r'\bprocess\.env\s*\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']')),
    ("js", re.compile(r'\bimport\.meta\.env\.([A-Za-z_][A-Za-z0-9_]*)')),
]

EXT_LANG = {".py":"python", ".js":"javascript", ".jsx":"javascript", ".ts":"typescript", ".tsx":"typescript"}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".pytest_cache"}

def scan_code(repo: Path) -> list[CodeUse]:
    results = []
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXT_LANG:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lang = EXT_LANG[path.suffix.lower()]
        rel = path.relative_to(repo).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern_lang, pattern in PATTERNS:
                if pattern_lang == "python" and lang != "python":
                    continue
                if pattern_lang == "js" and lang not in {"javascript", "typescript"}:
                    continue
                for match in pattern.finditer(line):
                    results.append(CodeUse(match.group(1), rel, lineno, lang))
    # deterministic de-duplication
    return sorted(set(results), key=lambda x: (x.key, x.file, x.line))

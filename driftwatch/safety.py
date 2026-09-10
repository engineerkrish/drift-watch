import re

SECRET_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|API[_-]?KEY|PRIVATE[_-]?KEY|CREDENTIAL|AUTH)",
    re.I,
)

def is_secret_key(key: str) -> bool:
    return bool(SECRET_RE.search(key))

def safe_type(value: str) -> str:
    """Infer type/format. The caller should immediately discard value."""
    if value is None or value == "":
        return "empty"
    v = value.strip()
    if v.lower() in {"true", "false"}:
        return "boolean"
    if re.fullmatch(r"[+-]?(?:\d+\.?\d*|\.\d+)", v):
        return "numeric"
    if re.match(r"^(https?|postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?)://", v, re.I):
        return "url"
    return "string"

def redact_for_internal_error(text: str) -> str:
    # Never echo potentially sensitive content in errors.
    return re.sub(r"(?i)(=)([^\s,;]+)", r"\1[REDACTED]", text)

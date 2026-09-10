from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class CodeUse:
    key: str
    file: str
    line: int
    language: str

@dataclass(frozen=True)
class ConfigKey:
    key: str
    environment: str
    source: str
    value_type: str

@dataclass(frozen=True)
class Finding:
    key: str
    category: str
    severity: str
    used_at: Optional[str]
    defined_in: tuple[str, ...]
    missing_in: tuple[str, ...]
    sources: tuple[str, ...]
    note: str
    fingerprint: str = field(default="")

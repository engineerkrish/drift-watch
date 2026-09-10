from pathlib import Path
import re
import yaml
from dotenv import dotenv_values
from ..models import ConfigKey
from ..safety import safe_type


ENV_ALIASES = {
    "dev": "development",
    "development": "development",
    "stage": "staging",
    "staging": "staging",
    "prod": "production",
    "production": "production",
}


def normalize_env(name: str) -> str:
    n = name.lower()
    for k, v in ENV_ALIASES.items():
        if k in n:
            return v
    return "unknown"


def infer_env_from_filename(path: Path) -> str:
    name = path.name.lower()

    if name.startswith(".env."):
        return normalize_env(name.split(".")[-1])

    return normalize_env(
        path.stem.replace("docker-compose", "").replace(".", "")
    )


def _raw_dotenv_types(path: Path) -> dict[str, str]:
    """
    Read only the syntax of .env assignments so we can distinguish:

        MAX_RETRY_COUNT=5       -> number
        MAX_RETRY_COUNT="5"     -> string

    We intentionally NEVER return or store the actual value.
    python-dotenv is still used for proper .env parsing below.
    """

    types = {}

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return types

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        match = re.match(
            r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$",
            stripped,
        )

        if not match:
            continue

        key = match.group(1)
        raw_rhs = match.group(2).strip()

        # Empty values are strings.
        if not raw_rhs:
            types[key] = "string"
            continue

        # Quoted values are intentionally classified as strings.
        if (
            len(raw_rhs) >= 2
            and raw_rhs[0] in {"'", '"'}
            and raw_rhs[-1] == raw_rhs[0]
        ):
            types[key] = "string"
            continue

        # Unquoted values use our normal safe type inference.
        types[key] = safe_type(raw_rhs)

    return types


def scan_dotenv(path: Path, environment: str, repo: Path) -> list[ConfigKey]:
    # python-dotenv handles comments, quoted values, embedded '='
    # and normal .env syntax.
    parsed = dotenv_values(path, interpolate=False)

    # Separately inspect the source syntax so quoted numeric values
    # remain distinguishable from unquoted numeric values.
    raw_types = _raw_dotenv_types(path)

    out = []

    for key, raw in parsed.items():
        if not key:
            continue

        value_type = raw_types.get(
            str(key),
            safe_type("" if raw is None else str(raw)),
        )

        # Raw values are intentionally NEVER returned or stored.
        out.append(
            ConfigKey(
                str(key),
                environment,
                path.relative_to(repo).as_posix(),
                value_type,
            )
        )

    return out


def _walk_yaml_values(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield str(k), v
            yield from _walk_yaml_values(v)

    elif isinstance(node, list):
        for item in node:
            yield from _walk_yaml_values(item)


def scan_yaml(path: Path, environment: str, repo: Path) -> list[ConfigKey]:
    try:
        docs = list(
            yaml.safe_load_all(
                path.read_text(encoding="utf-8")
            )
        )
    except Exception as exc:
        raise ValueError(
            f"Could not parse YAML config source: {path}"
        ) from exc

    out = []

    for doc in docs:
        if not isinstance(doc, dict):
            continue

        # Kubernetes ConfigMap/Secret data/stringData
        if doc.get("kind") in {"ConfigMap", "Secret"}:
            for field in ("data", "stringData"):
                data = doc.get(field, {})

                if isinstance(data, dict):
                    for key, raw in data.items():
                        out.append(
                            ConfigKey(
                                str(key),
                                environment,
                                path.relative_to(repo).as_posix(),
                                safe_type(
                                    "" if raw is None else str(raw)
                                ),
                            )
                        )

        # Docker Compose service environment blocks.
        services = doc.get("services", {})

        if isinstance(services, dict):
            for service in services.values():
                if not isinstance(service, dict):
                    continue

                env = service.get("environment", {})

                if isinstance(env, dict):
                    for key, raw in env.items():

                        # ${FOO} references a key without exposing
                        # any resolved value.
                        if isinstance(raw, str):
                            m = re.fullmatch(
                                r"\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}",
                                raw.strip(),
                            )

                            key_type = (
                                "reference"
                                if m
                                else safe_type(raw)
                            )
                        else:
                            key_type = safe_type(
                                "" if raw is None else str(raw)
                            )

                        out.append(
                            ConfigKey(
                                str(key),
                                environment,
                                path.relative_to(repo).as_posix(),
                                key_type,
                            )
                        )

                elif isinstance(env, list):
                    for item in env:
                        if not isinstance(item, str):
                            continue

                        key = item.split("=", 1)[0]
                        raw = (
                            item.split("=", 1)[1]
                            if "=" in item
                            else ""
                        )

                        out.append(
                            ConfigKey(
                                key,
                                environment,
                                path.relative_to(repo).as_posix(),
                                safe_type(raw),
                            )
                        )

    return out


def scan_configs(repo: Path) -> list[ConfigKey]:
    results = []

    for path in repo.rglob("*"):
        if not path.is_file():
            continue

        name = path.name.lower()

        if name.startswith(".env"):
            env = infer_env_from_filename(path)

            if env != "unknown":
                results.extend(
                    scan_dotenv(path, env, repo)
                )

        elif name.endswith((".yml", ".yaml")) and (
            "compose" in name
            or "k8s" in str(path).lower()
            or "kubernetes" in str(path).lower()
        ):
            env = infer_env_from_filename(path)

            if env == "unknown":
                env = "development"

            results.extend(
                scan_yaml(path, env, repo)
            )

    return results
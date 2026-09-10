import hashlib
from collections import defaultdict
from ..models import Finding

SEVERITY = {"missing":"critical", "type-mismatch":"warning", "orphaned":"info"}

def _fp(key, category, missing, defined, types):
    raw = "|".join([key, category, ",".join(missing), ",".join(defined), repr(sorted(types.items()))])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def build_findings(used, configs, environments=("development","staging","production")):
    used_by_key = defaultdict(list)
    for u in used:
        used_by_key[u.key].append(u)
    cfg_by_key_env = defaultdict(list)
    for c in configs:
        cfg_by_key_env[(c.key, c.environment)].append(c)

    findings = []
    all_keys = sorted(set(used_by_key) | {c.key for c in configs})
    for key in all_keys:
        defined = tuple(sorted({env for (k, env) in cfg_by_key_env if k == key}))
        missing = tuple(env for env in environments if (key, env) not in cfg_by_key_env)
        uses = used_by_key.get(key, [])
        if uses and missing:
            u = uses[0]
            fp = _fp(key, "missing", missing, defined, {})
            findings.append(Finding(
                key, "missing", "critical", f"{u.file}:{u.line}", defined, missing,
                tuple(sorted({c.source for (k,e), cs in cfg_by_key_env.items() if k == key for c in cs})),
                "Referenced directly; no definition was found in the missing environment(s).", fp
            ))
        if not uses and defined:
            fp = _fp(key, "orphaned", (), defined, {})
            findings.append(Finding(
                key, "orphaned", "info", None, defined, (),
                tuple(sorted({c.source for (k,e), cs in cfg_by_key_env.items() if k == key for c in cs})),
                "Defined in configuration, but no code reference was found.", fp
            ))
        if uses and len(defined) == len(environments):
            types = {}
            for env in environments:
                ts = {c.value_type for c in cfg_by_key_env[(key, env)]}
                types[env] = ",".join(sorted(ts))
            # references are treated as unknown rather than a mismatch
            known = {v for v in types.values() if v not in {"reference",""}}
            if len(known) > 1:
                u = uses[0]
                fp = _fp(key, "type-mismatch", (), defined, types)
                findings.append(Finding(
                    key, "type-mismatch", "warning", f"{u.file}:{u.line}", defined, (),
                    tuple(sorted({c.source for (k,e), cs in cfg_by_key_env.items() if k == key for c in cs})),
                    f"Inferred type differs across environments: {', '.join(f'{e}={types[e]}' for e in environments)}.",
                    fp
                ))
    return sorted(findings, key=lambda f: ({"critical":0,"warning":1,"info":2}[f.severity], f.key))

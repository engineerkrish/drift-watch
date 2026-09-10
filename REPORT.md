# Drift Watch — Hackathon Report

## 1. What we built

Drift Watch independently scans source code for configuration references and scans environment configuration sources, then deterministically compares the two sets. It reports missing, orphaned and type-mismatch findings with real file/line or config-source anchors. Raw secret values never enter the reporting or persistence layers. The tool also fingerprints findings so repeated unchanged runs do not spam new alerts. The demo supports Python, JavaScript/TypeScript, `.env` and Docker Compose.

## Architecture

`code scanner → config scanner → drift engine → safety boundary → state/change detector → terminal + Markdown reporter`

## 2. Detection logic

| Category | Detection |
|---|---|
| Missing | `used_in_code - defined_in_environment` |
| Orphaned | `defined_in_environment - used_in_code` |
| Type mismatch | Same key is present in all environments but inferred types differ |

## 3. Methods and decisions

- `.env`: parsed with `python-dotenv`; raw values are immediately converted to a type and are not returned.
- YAML: parsed with `PyYAML`; Docker Compose `environment` and Kubernetes ConfigMap/Secret data are supported.
- Code tracing: deterministic regexes for direct access patterns; tracing stops at direct access and does not claim full config-object indirection.
- No-repeat-noise: SHA-256 fingerprint of key/category/environment/type pattern is persisted in `.driftwatch/state.json`.
- LLM: not used; deterministic scanning gives grounded, reproducible findings and avoids external secret exposure.
- Environment-specific intent: this MVP reports differences honestly; a future allowlist/heuristic can classify intentional feature flags.

## 4. Safety

The reporter never receives raw values. Secret-shaped keys are treated exactly like other keys and their values are never printed. The demo includes fake secret-shaped values and a leak check consists of searching generated output/state for known fake values.

## 5. Results

Test these scenarios during the demo:

1. Missing `PAYMENTS_WEBHOOK_SECRET` in staging — expected critical.
2. Orphaned `LEGACY_CACHE_HOST` — expected info.
3. Type mismatch `MAX_RETRY_COUNT` — expected warning.
4. Secret-shaped `STRIPE_API_KEY` — value must never appear.
5. Quoted value containing `=` — parser must succeed.
6. Clean fixture — expected no drift.

## 6. Limitations and next steps

Direct config-object indirection is intentionally outside the trace boundary. Environment-specific intent currently requires an allowlist/heuristic. CI secret stores are not scanned because they do not expose values through the local filesystem.

## 7. How to run

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python -m driftwatch scan fixtures/demo
python -m driftwatch scan fixtures/clean
```

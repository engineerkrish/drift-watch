# 🔍 Drift Watch

### Configuration Drift Detective

> **Find configuration drift before it finds you.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-4%20Passed-2ea44f?logo=pytest\&logoColor=white)](https://pytest.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/engineerkrish/drift-watch/drift-watch.yml?branch=main\&label=CI)](https://github.com/engineerkrish/drift-watch/actions)

---

## 🚀 What is Drift Watch?

**Drift Watch** is a deterministic DevOps tool that detects **configuration drift** between application source code and the environments where the application runs.

It independently answers two questions:

```text
What configuration does the APPLICATION actually use?
                    +
What configuration does each ENVIRONMENT actually define?
                    ↓
             DRIFT WATCH
                    ↓
     Are they still consistent?
```

It detects three important classes of configuration drift:

* 🔴 **Missing Configuration**
* 🟡 **Type Mismatch**
* 🔵 **Orphaned Configuration**

> **Catch configuration problems before they become deployment or runtime failures.**

---

# 💥 The Problem

Modern applications rarely keep configuration in one place.

Configuration can be scattered across:

```text
Application Source Code
        │
        ├── Python
        ├── JavaScript
        └── TypeScript
                │
                ▼
        Environment Config
        │
        ├── .env
        ├── Docker Compose
        └── Kubernetes
                │
                ▼
      Development / Staging / Production
```

A typical failure looks like this:

```text
Developer adds a new configuration key
                ↓
Code uses the key
                ↓
Development defines it       ✅
Staging forgets it            ❌
Production defines it        ✅
                ↓
Deployment / runtime failure
```

The application can work perfectly on a developer's machine while failing in another environment.

---

# 💡 Our Solution

Drift Watch treats configuration as a **contract** between application code and runtime environments.

```text
                 APPLICATION
                    CODE
                     │
                     │
              What does code use?
                     │
                     ▼
              ┌──────────────┐
              │ DRIFT WATCH  │
              │    ENGINE    │
              └──────────────┘
                     ▲
                     │
              What is defined?
                     │
                     │
               ENVIRONMENTS
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   Development    Staging    Production
```

Drift Watch independently scans both sides, correlates them, and reports inconsistencies.

---

# ⚙️ How It Works

## 1️⃣ Scan Application Code

Drift Watch scans source code for direct configuration access.

### Python

```python
os.getenv("DATABASE_URL")

os.environ.get("API_BASE_URL")

os.environ["PORT"]
```

### JavaScript / TypeScript

```javascript
process.env.DATABASE_URL

process.env["API_BASE_URL"]

import.meta.env.VITE_API_URL
```

The scanner records:

* Configuration Key
* Source File
* Line Number
* Programming Language

It does **not** need the actual configuration value.

---

## 2️⃣ Scan Configuration Sources

Drift Watch scans configuration definitions from:

* `.env`
* Docker Compose YAML
* Kubernetes ConfigMap
* Kubernetes Secret

Values are converted into safe metadata such as inferred type.

**Raw configuration values are not passed to the reporting layer.**

---

## 3️⃣ 🔗 Correlate

The core idea is:

```text
CODE USES
    │
    ▼
PAYMENTS_WEBHOOK_SECRET
    │
    ├──────── Development ✅
    ├──────── Staging      ❌
    └──────── Production   ✅
```

Drift Watch compares:

```text
Keys used by code
        VS
Keys defined by environments
```

---

# 🚨 4️⃣ Detect Configuration Drift

| Finding              | Meaning                                                        | Severity     |
| -------------------- | -------------------------------------------------------------- | ------------ |
| 🔴 **Missing**       | Code uses a key that is absent from an environment             | **Critical** |
| 🟡 **Type Mismatch** | A key exists across environments but its inferred type differs | **Warning**  |
| 🔵 **Orphaned**      | Configuration is defined but no direct code reference exists   | **Info**     |

### 🔴 Missing Configuration

```text
PAYMENTS_WEBHOOK_SECRET

Development:  ✅
Staging:      ❌
Production:   ✅
```

```text
CRITICAL | missing
```

### 🟡 Type Mismatch

```text
Development:
MAX_RETRY_COUNT=5
        ↓
numeric

Staging:
MAX_RETRY_COUNT=5
        ↓
numeric

Production:
MAX_RETRY_COUNT="5"
        ↓
string
```

```text
WARNING | type-mismatch
```

### 🔵 Orphaned Configuration

```text
LEGACY_CACHE_HOST
```

If no application code directly uses it:

```text
INFO | orphaned
```

---

# 🧠 Detection Logic

```text
Missing:
used_in_code - defined_in_environment

Orphaned:
defined_in_environment - used_in_code

Type Mismatch:
same key exists across environments
+
inferred types differ
```

The detection engine is deterministic, reproducible, and grounded in real source/configuration references.

---

# 🏗️ Architecture

```text
┌──────────────────────────────┐
│       APPLICATION CODE       │
│                              │
│    Python / JavaScript / TS  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        CODE SCANNER          │
│                              │
│ Detect direct config access  │
└──────────────┬───────────────┘
               │
               ▼
        ┌──────────────┐
        │ DRIFT ENGINE │
        │              │
        │   Correlate  │
        │    Detect    │
        └──────┬───────┘
               │
       ┌───────┼────────┐
       │       │        │
       ▼       ▼        ▼
    Missing  Type     Orphaned
             Mismatch
               │
               ▼
┌──────────────────────────────┐
│         REPORTER             │
│                              │
│ Terminal + Markdown Report   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       STATE TRACKING         │
│                              │
│ SHA-256 Finding Fingerprints │
└──────────────────────────────┘


Configuration Sources
─────────────────────

.env
Docker Compose
Kubernetes ConfigMap / Secret
          │
          ▼
┌──────────────────────────────┐
│       CONFIG SCANNER         │
└──────────────────────────────┘
```

---

# 🔐 Security by Design

Secret safety is a core requirement of Drift Watch.

### 🚫 Raw values are never reported

The reporting layer works with metadata such as:

```text
Key
Type
Environment
Location
Source
```

### 🔑 Secret-shaped keys

Examples include:

```text
SECRET
TOKEN
PASSWORD
API_KEY
PRIVATE_KEY
CREDENTIAL
```

Their values are never printed.

### 💾 State safety

State tracking stores finding fingerprints rather than configuration values.

```text
Configuration Value
        ❌
        │
        X
        │
        ▼
Safe Finding Metadata
        │
        ▼
SHA-256 Fingerprint
```

> **We prove that a configuration exists or is missing without proving it by printing the secret.**

---

# 🔁 No-Repeat Noise

An unchanged finding should not repeatedly appear as a brand-new issue.

Drift Watch generates a stable fingerprint from relevant finding metadata.

```text
             FIRST SCAN
                 │
                 ▼
          Finding detected
                 │
                 ▼
        Fingerprint generated
                 │
                 ▼
          State is stored
                 │
                 ▼
            SECOND SCAN
                 │
                 ▼
       Same fingerprint found
                 │
                 ▼
        Existing finding
                 │
                 ▼
           No NEW alert
```

The system can distinguish between:

```text
New
Still unresolved
Resolved
```

---

# 🧪 Testing

## 4 Tests — 4 Passed ✅

Verified automated smoke-test suite:

| # | Test Case               | What It Verifies                                   | Result |
| - | ----------------------- | -------------------------------------------------- | ------ |
| 1 | Demo drift detection    | Missing and orphaned findings are detected         | ✅ PASS |
| 2 | Type mismatch detection | `MAX_RETRY_COUNT` type drift is detected           | ✅ PASS |
| 3 | Secret safety           | Known fake secret values do not appear in findings | ✅ PASS |
| 4 | Repeatability           | Identical scans produce identical fingerprints     | ✅ PASS |

Verified result:

```text
4 passed
```

---

# 🎬 Demo Scenarios

## 1. Missing Configuration

```text
PAYMENTS_WEBHOOK_SECRET
```

Expected:

```text
CRITICAL | missing
```

Reason:

```text
Used by code
but missing from staging
```

---

## 2. Type Mismatch

```text
MAX_RETRY_COUNT
```

Expected:

```text
WARNING | type-mismatch
```

Reason:

```text
Development = numeric
Staging     = numeric
Production  = string
```

---

## 3. Orphaned Configuration

```text
LEGACY_CACHE_HOST
```

Expected:

```text
INFO | orphaned
```

Reason:

```text
Defined in configuration
but not directly referenced by code
```

---

## 4. Secret Safety

Example:

```text
STRIPE_API_KEY
```

The key can be detected, but its actual value must never appear in:

* Terminal output
* Markdown report
* State file
* Findings

---

## 5. Quoted Configuration Value

Example:

```text
MESSAGE="hello=world"
```

The parser should correctly handle the `=` character inside the quoted value.

---

## 6. Clean Configuration

The `fixtures/clean` directory represents a configuration setup without intentional drift.

Expected:

```text
No drift findings
```

> The four automated tests above are the verified smoke-test suite. The additional scenarios are documented demo/validation cases.

---

# 📊 Example Output

```text
CRITICAL | missing | PAYMENTS_WEBHOOK_SECRET
Location: src/payments/webhook.ts:2
Missing: staging

WARNING | type-mismatch | MAX_RETRY_COUNT
Location: src/http/client.py:4
Types: development=numeric, staging=numeric, production=string

INFO | orphaned | LEGACY_CACHE_HOST
Defined in configuration but not referenced directly
```

The tool identifies **what is wrong and where** without exposing the actual secret value.

---

# 🤖 CI/CD Integration

Drift Watch includes a GitHub Actions workflow.

The pipeline performs:

```text
Checkout Repository
        ↓
Install Dependencies
        ↓
Run Automated Tests
        ↓
Scan Clean Configuration
        ↓
Generate Drift Watch Report
        ↓
Publish Report
```

The workflow provides automated validation on repository changes.

A critical drift finding produces a **non-zero exit code**, allowing Drift Watch to act as a CI/CD quality gate.

---

# 🧰 Technology Stack

| Component            | Technology           |
| -------------------- | -------------------- |
| Programming Language | Python 3.12          |
| Code Scanner         | Deterministic Regex  |
| `.env` Parser        | python-dotenv        |
| YAML Parser          | PyYAML               |
| Terminal UI          | Rich                 |
| Testing              | pytest               |
| CI/CD                | GitHub Actions       |
| Reporting            | Markdown             |
| State Tracking       | SHA-256 fingerprints |

### Why no LLM?

Drift Watch intentionally uses deterministic scanning for the MVP.

```text
Deterministic Results
        +
Reproducible Detection
        +
Grounded File/Line References
        +
Predictable Testing
        +
Reduced Secret Exposure
```

An LLM is not required for the core problem.

---

# 📁 Project Structure

```text
drift-watch/
│
├── driftwatch/
│   ├── scanner/
│   │   ├── code_scanner.py
│   │   └── config_scanner.py
│   │
│   ├── engine/
│   │   ├── drift_engine.py
│   │   └── state.py
│   │
│   ├── reporter/
│   │   ├── terminal.py
│   │   └── markdown.py
│   │
│   ├── models.py
│   ├── safety.py
│   └── cli.py
│
├── fixtures/
│   ├── clean/
│   └── demo/
│
├── tests/
│   └── smoke_test.py
│
├── .github/
│   └── workflows/
│       └── drift-watch.yml
│
├── REPORT.md
├── requirements.txt
└── README.md
```

---

# ▶️ Run Locally

### Clone the repository

```bash
git clone https://github.com/engineerkrish/drift-watch.git
cd drift-watch
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Run the demo

```powershell
python -m driftwatch scan fixtures/demo
```

### Run the clean fixture

```powershell
python -m driftwatch scan fixtures/clean
```

### Run automated tests

```powershell
python -m pytest tests
```

Expected:

```text
4 passed
```

---

# 🧠 Design Decisions

### Deterministic over probabilistic

The MVP does not depend on an LLM.

This keeps the detection:

* Reproducible
* Explainable
* Testable
* Grounded

### Safety before convenience

Configuration values are not propagated into reporting or persistence.

### Honest trace boundary

The scanner focuses on direct configuration access and does not claim to understand complex config-object indirection.

### Environment differences are not automatically assumed to be bugs

The MVP reports differences honestly. Future versions can add allowlists or heuristics for intentional environment-specific configuration.

---

# ⚠️ Current Limitations

Drift Watch is an intentionally focused MVP.

### Direct configuration access

The current code scanner focuses on direct access patterns.

Complex configuration-object indirection is outside the current trace boundary.

### Environment-specific intent

Not every difference between environments is necessarily a bug.

For example:

```text
Feature enabled in Production
Feature disabled in Development
```

may be intentional.

The current MVP reports the difference honestly instead of pretending to understand business intent.

### CI Secret Stores

CI/CD secret stores are not scanned because their values are not exposed through the local filesystem.

These boundaries are documented deliberately so the project does not claim coverage it does not provide.

---

# 📖 Documentation

### Technical Report

See [`REPORT.md`](REPORT.md) for:

* Architecture
* Detection logic
* Methods and design decisions
* Security approach
* Test scenarios
* Results
* Limitations
* How to run
* Development process

### GitHub Actions

See [`.github/workflows/drift-watch.yml`](.github/workflows/drift-watch.yml).

---

# 🏆 Why Drift Watch?

Configuration drift is easy to create and surprisingly difficult to notice.

A developer can add one environment variable today and forget to add it somewhere else.

A deployment can then fail hours or days later.

Drift Watch moves that detection earlier:

```text
Developer changes code
        ↓
Configuration changes
        ↓
        DRIFT WATCH
             ↓
      Detect drift
             ↓
         Fix early
             ↓
   Confident deployment
```

---

# 🎯 Project Takeaway

> ## Same Code. Different Environments. No Surprises.

Drift Watch treats configuration as a contract between application code and runtime environments.

It independently observes:

```text
What the application USES
            +
What environments DEFINE
            ↓
       DRIFT WATCH
            ↓
What is MISSING?
What is MISMATCHED?
What is ORPHANED?
```

And it does this while keeping configuration values out of the reporting and persistence layers.

---

# 🔍 Drift Watch

### Configuration Drift Detective

**Detect • Prevent • Stay Secure**

---

⭐ Built as a focused DevOps / configuration-security hackathon project.

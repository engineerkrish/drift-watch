# 🔍 Drift Watch

### Configuration Drift Detective

> Detect configuration drift across source code and environments — without exposing secrets.

Drift Watch is a deterministic DevOps security tool that compares the configuration a codebase **expects** with the configuration that environments **actually define**.

It identifies configuration drift before it becomes a deployment failure.

---

## 🚨 The Problem

Configuration is usually scattered across multiple places:

- Application source code
- `.env` files
- Docker Compose files
- Kubernetes manifests
- Different environment configurations

This creates a common failure mode:

```text
Code expects a configuration key
             ↓
Environment does not define it
             ↓
Deployment / runtime failure
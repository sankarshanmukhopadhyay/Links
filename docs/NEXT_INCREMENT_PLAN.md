# Next Increment Plan — Operational Hardening + Governance Readiness

This plan converts the current repo into something that can be deployed with fewer foot-guns, and sets up the follow-on work for pull-based, signed policy reconciliation.

This plan is derived from the attached evaluation notes and is intended to be applied as a single cohesive increment.


## Status
**Completed:** v0.11.0 baseline shipped (2026-02-27)

This plan is now treated as “done” for the hardening items it covered. Remaining work has been moved into the next increment below.

---
## Next Increment (draft) — Pull-based Reconciliation + Storage Abstraction

This increment focuses on closing the gap between “signed feeds exist” and “nodes can safely converge”:

### 1) Pull-based policy reconciliation (end-to-end)
- Implement:
  - `GET /villages/{id}/policy/latest`
  - `GET /villages/{id}/policy/updates?since=...` (paged)
- Add `links policy pull --apply` with deterministic reconciliation rules
- Produce fork/conflict report artifacts suitable for audit

### 2) Storage abstraction + optional SQLite backend
- Introduce a pluggable storage interface (JSONL default)
- Optional SQLite backend behind a feature flag
- Atomic policy apply transaction boundary (apply + audit + indexes)

### 3) Observability automation
- Scheduled drift checks (cron-friendly command + example)
- Signed transparency log checkpoints (periodic snapshot)


## Confirmation checkpoint (before you merge)

Please confirm these scope decisions:
- [x] We prioritized **operational hardening** (packaging, safe persistence, rate limiting, quarantine re-check, path sanitization, TLS posture).
- [x] We shipped a governance substrate baseline separately (v0.11.0); **full pull-based reconciliation** remains the next increment.
- [x] We use **POSIX file locking** for JSONL (Linux/macOS), with a note to migrate to SQLite later if needed.

## Scope — what changes in this increment

### A. Packaging & install correctness
- Fix `pyproject.toml` to ensure `links` is installable and the CLI entrypoint works.
- Ensure declared dependencies include FastAPI/Uvicorn/Pydantic/Typer/NaCl/Requests.

### B. Persistence safety under concurrency
- Add a tiny file-lock utility for JSONL append operations.
- Use locked append for:
  - flattened claims index
  - audit log
  - village members + revocations + policy history

### C. Quarantine approval safety
- Quarantine approve must **re-check current village policy** before allowing ingestion.
- Reject or keep in quarantine if policy no longer allows it.

### D. Security hygiene
- Sanitize `village_id` to prevent path traversal (`^[a-zA-Z0-9_-]+$`).
- Add basic in-memory rate limiting middleware using village policy `rate_limit_per_min`.
- Improve TLS posture: warn when binding to non-loopback; document “run behind TLS terminator” expectation.

### E. Documentation cleanup
- Ensure README contains **no internal project-management terms** (phases/baseline/etc).
- Add operational notes for TLS, tokens, rate limiting, and quarantine.

## Follow-on increment (planned, not implemented here)
- Make policy updates fully pull-based:
  - `GET /villages/{id}/policy/latest`
  - `GET /villages/{id}/policy/updates?since=…`
  - `links policy pull --apply` reconciliation rules


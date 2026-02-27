# Next Increment Plan — Operational Hardening + Governance Readiness

This plan converts the current repo into something that can be deployed with fewer foot-guns, and sets up the follow-on work for pull-based, signed policy reconciliation.

This plan is derived from the attached evaluation notes and is intended to be applied as a single cohesive increment.

## Confirmation checkpoint (before you merge)

Please confirm these scope decisions:
- [ ] We will prioritize **operational hardening** first (packaging, safe persistence, rate limiting, quarantine re-check, path sanitization, TLS posture).
- [ ] We will ship **pull-based policy reconciliation** as the *next* increment after this (not bundled into this hardening release).
- [ ] We accept a pragmatic approach for concurrency: **POSIX file locking** for JSONL (Linux/macOS), with a note to migrate to SQLite later if needed.

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


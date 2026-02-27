# Links Roadmap

This document captures the intended direction of the Links project.  
It is intentionally schedule-free. Items move forward based on architectural readiness, contributor bandwidth, and operational priority.

## Status legend
- ✅ Completed (baseline shipped)
- 🟡 Partial (scaffolded; needs hardening)
- 🔜 Planned (not implemented yet)

_Last updated: 2026-02-27 (v0.11.0 baseline)_


---

## 1. Governance & Policy Evolution

### 1.1 Quorum Governance Enhancements
**Status:** ✅ Completed (v0.11.0)
- Support weighted quorum (e.g., weighted signers instead of simple M-of-N)
- Support role-based quorum sets (e.g., at least one “core” + one “external” signer)
- Add explicit quorum metadata into policy update artifacts for audit clarity

### 1.2 Policy Diff & Review
**Status:** ✅ Completed (v0.11.0)
- Add structured policy diff tooling
- Provide machine-readable policy change summaries
- Add “proposal → approval → activation” lifecycle states

### 1.3 Policy Rollback & Versioning
**Status:** ✅ Completed (v0.11.0)
- First-class policy version identifiers
- Deterministic rollback to prior policy hash
- Explicit “activation height” or activation timestamp semantics

---

## 2. Distributed Policy Substrate

### 2.1 Pull Model Hardening
**Status:** 🟡 Partial (v0.11.0 baseline: signed manifests + pagination hooks; needs full pull reconciliation rules)
- Signed policy feed manifests
- Feed integrity metadata (Merkle root or hash chain)
- Pagination and large-history optimization

### 2.2 Federation & Multi-Node Reconciliation
**Status:** 🟡 Partial (v0.11.0 baseline: conflict/fork detection; gossip propagation planned)
- Cross-node reconciliation conflict detection
- Explicit fork detection reporting
- Optional gossip-based propagation

### 2.3 Trust Anchors
**Status:** 🟡 Partial (v0.11.0 baseline: registry + rotate/revoke primitives; operational playbooks planned)
- Village-level trust anchor registry
- Anchor rotation procedures
- Explicit anchor revocation workflow

---

## 3. Assurance & Observability

### 3.1 Policy Audit Trails
**Status:** 🟡 Partial (v0.11.0 baseline: JSON/CSV export + digest; event taxonomy and signing hardening planned)
- Structured audit export (JSON/CSV)
- Policy change event classification
- Audit digest signing

### 3.2 Drift Monitoring
**Status:** 🟡 Partial (v0.11.0 baseline: CLI drift check + severity + webhook hook; periodic automation planned)
- Periodic automated drift checks
- Drift severity classification
- Alert hooks (webhook or CLI-based triggers)

### 3.3 Governance Transparency
**Status:** 🟡 Partial (v0.11.0 baseline: transparency log + snapshots; read-only public mode hardening planned)
- Read-only public policy endpoint option
- Signed policy transparency log
- Reproducible policy history snapshots

---

## 4. Operational Hardening

### 4.1 Storage Layer Evolution
**Status:** 🔜 Planned (SQLite backend + abstraction + atomic transactions)
- Optional SQLite backend
- Pluggable storage abstraction layer
- Atomic policy apply transactions

### 4.2 Deployment Profiles
**Status:** 🟡 Partial (v0.11.0 baseline docs + container-ready example; production templates planned)
- “Single-node dev” profile
- “Production hardened” profile
- Container-ready configuration examples

### 4.3 Performance & Limits
**Status:** 🟡 Partial (v0.11.0 baseline: rate limiting + streaming patterns + load script; full harness planned)
- Configurable rate limit strategies
- Memory-safe streaming for large claim sets
- Load testing harness

---

## 5. Security & Risk Controls

### 5.1 Advanced Signature Controls
**Status:** 🔜 Planned (HSM/hardware signing, enforced rotation, expiry)
- Hardware-backed signing integration
- Key rotation enforcement
- Expiring policy updates

### 5.2 Abuse & Misuse Controls
**Status:** 🟡 Partial (v0.11.0 baseline: quotas + replay protection + signed denials best-effort; hardening planned)
- Village-level submission quotas
- Replay protection improvements
- Signed denial / rejection artifacts

### 5.3 Cryptographic Agility
**Status:** 🟡 Partial (v0.11.0 baseline: alg field + guardrails; broader algo support + deprecation lifecycle planned)
- Algorithm negotiation field
- Support for additional signature algorithms
- Explicit deprecation lifecycle

---

## 6. Ecosystem & Interoperability

### 6.1 External Registry Integration
**Status:** 🟡 Partial (v0.11.0 baseline: import/export CLI; bridging patterns planned)
- Import/export trust registry artifacts
- Registry-to-village bridging patterns

### 6.2 Standardization Alignment
**Status:** 🔜 Planned (schema refinement, JSON-LD optional contexts, conformance suite)
- Schema refinement for policy update artifact
- JSON-LD or canonical context support (optional)
- Conformance test suite for policy governance

### 6.3 Tooling & SDK
**Status:** 🟡 Partial (v0.11.0 baseline: Python SDK + minimal client + example; dedicated integration repo planned)
- Python SDK wrapper
- Minimal HTTP client library
- Example integration repo

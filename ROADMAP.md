# Links Roadmap

This document captures the intended direction of the Links project.  
It is intentionally schedule-free. Items move forward based on architectural readiness, contributor bandwidth, and operational priority.

---

## 1. Governance & Policy Evolution

### 1.1 Quorum Governance Enhancements
- Support weighted quorum (e.g., weighted signers instead of simple M-of-N)
- Support role-based quorum sets (e.g., at least one “core” + one “external” signer)
- Add explicit quorum metadata into policy update artifacts for audit clarity

### 1.2 Policy Diff & Review
- Add structured policy diff tooling
- Provide machine-readable policy change summaries
- Add “proposal → approval → activation” lifecycle states

### 1.3 Policy Rollback & Versioning
- First-class policy version identifiers
- Deterministic rollback to prior policy hash
- Explicit “activation height” or activation timestamp semantics

---

## 2. Distributed Policy Substrate

### 2.1 Pull Model Hardening
- Signed policy feed manifests
- Feed integrity metadata (Merkle root or hash chain)
- Pagination and large-history optimization

### 2.2 Federation & Multi-Node Reconciliation
- Cross-node reconciliation conflict detection
- Explicit fork detection reporting
- Optional gossip-based propagation

### 2.3 Trust Anchors
- Village-level trust anchor registry
- Anchor rotation procedures
- Explicit anchor revocation workflow

---

## 3. Assurance & Observability

### 3.1 Policy Audit Trails
- Structured audit export (JSON/CSV)
- Policy change event classification
- Audit digest signing

### 3.2 Drift Monitoring
- Periodic automated drift checks
- Drift severity classification
- Alert hooks (webhook or CLI-based triggers)

### 3.3 Governance Transparency
- Read-only public policy endpoint option
- Signed policy transparency log
- Reproducible policy history snapshots

---

## 4. Operational Hardening

### 4.1 Storage Layer Evolution
- Optional SQLite backend
- Pluggable storage abstraction layer
- Atomic policy apply transactions

### 4.2 Deployment Profiles
- “Single-node dev” profile
- “Production hardened” profile
- Container-ready configuration examples

### 4.3 Performance & Limits
- Configurable rate limit strategies
- Memory-safe streaming for large claim sets
- Load testing harness

---

## 5. Security & Risk Controls

### 5.1 Advanced Signature Controls
- Hardware-backed signing integration
- Key rotation enforcement
- Expiring policy updates

### 5.2 Abuse & Misuse Controls
- Village-level submission quotas
- Replay protection improvements
- Signed denial / rejection artifacts

### 5.3 Cryptographic Agility
- Algorithm negotiation field
- Support for additional signature algorithms
- Explicit deprecation lifecycle

---

## 6. Ecosystem & Interoperability

### 6.1 External Registry Integration
- Import/export trust registry artifacts
- Registry-to-village bridging patterns

### 6.2 Standardization Alignment
- Schema refinement for policy update artifact
- JSON-LD or canonical context support (optional)
- Conformance test suite for policy governance

### 6.3 Tooling & SDK
- Python SDK wrapper
- Minimal HTTP client library
- Example integration repo

---

## Guiding Principles

- Deterministic reconciliation over implicit coordination
- Signed artifacts over implicit trust
- Explicit policy semantics over convention
- Evolvability without breaking existing artifacts
- Operational simplicity first, extensibility second

---

This roadmap is a working architectural memory of intended direction.  
It can evolve as governance, deployment realities, and ecosystem constraints evolve.

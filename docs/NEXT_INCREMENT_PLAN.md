# Next Increment Plan — Live Endpoints, Quorum Operationalization, and SDK Stabilization

The prior increment (v0.14.0) delivered transparency checkpoint signing and publication, a formal drift class taxonomy, and machine-readable capability declarations. All three modules have full test coverage and are independently usable.

## Objective

Advance from library-level capability to operator-visible, protocol-level surfaces. The three new modules need server integration points, and the quorum governance work needs to move from artifact-level scaffolding toward operational enforcement.

---

## Priority 1: Live HTTP endpoints for transparency and capability

### Target outcomes
- Add `GET /villages/{village_id}/transparency/checkpoint` to `server.py` so `fetch_peer_checkpoint` has a real target.
- Add `GET /nodes/capability` to serve the node's capability manifest over HTTP for peer discovery.
- Document the endpoint contract and add integration tests against a `TestClient`.

---

## Priority 2: Quorum operationalization

### Target outcomes
- Enforce weighted and role-based quorum checks at policy apply time, not just at verification time.
- Add operator-facing CLI for quorum inspection: which signers have signed, what weight total has been reached, what role requirements are met.
- Expand `docs/policy-governance.md` with worked examples for weighted and role-based quorum setups.

---

## Priority 3: SDK stabilization and surface documentation

### Target outcomes
- Publish a machine-readable surface map distinguishing stable, experimental, and internal-only modules.
- Add a `links.sdk` façade that re-exports the stable public API surface with stable import paths.
- Document breaking-change policy for the stable surface.

---

## Explicit non-goals for this increment

- Large architectural rewrites
- New storage backends beyond filesystem and SQLite
- Speculative standards work without a concrete operator use case
- Broad schema churn unrelated to the endpoint or quorum work

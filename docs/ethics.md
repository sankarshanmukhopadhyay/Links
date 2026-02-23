# Ethics & Safeguards

This repository implements *reputation-adjacent* infrastructure. That category is inherently high-risk. The default posture is **minimize harm** and **avoid unjustified inference**.

## Safeguard principles (operational)

1. Public data only (by default)
2. No hidden inference: claims are explicit; derivations are declared
3. Explainability as a requirement: artifacts must be inspectable
4. Purpose limitation: villages define scope and norms
5. Access control by default: village endpoints require bearer tokens
6. Minimization + retention controls: default sliding windows and retention bounds
7. Abuse readiness: recommend auditing, logging, and incident response

## Harms prevention strategy

- Prevent: policy allowlists (predicates), max window, signature verification, village-scoped visibility
- Detect: policy violation rejections, ingest logs (recommended), anomaly monitoring (recommended)
- Respond: rotate tokens, revoke members, quarantine bundles
- Recover: rebuild store from verified bundles and replay indexes

## Non-goals

- This does not assert “true reputation”.
- This does not create global rankings of people.
- This does not guarantee fairness across communities without governance.

## Issuer controls

Villages can restrict which issuers (public keys) may submit bundles. This reduces poisoning risk and supports explicit trust boundaries.

## Quarantine and review

Policy failures can be quarantined for review. This supports a human-in-the-loop safety valve for valid-but-harmful or context-mismatched bundles.

# Policy Governance

Villages define a policy perimeter for claim acceptance and exchange. This repository supports policy updates via:

- Admin-gated API endpoint (`POST /villages/{village_id}/policy`)
- Optional signed policy update artifacts (Ed25519)

## Why signed policy updates?

Bearer tokens authenticate an operator. Signatures add:
- change provenance
- deterministic review and replay
- compatibility with offline governance workflows (PR review + artifact approval)

## Suggested operating model

- Maintain policy updates as artifacts committed to version control.
- Require signatures in higher risk deployments (`require_policy_signature=true`).
- Restrict policy signers (`policy_signer_allowlist`) to an explicit set of keys.
- Log and review all policy changes via the audit log.

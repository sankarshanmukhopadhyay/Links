# Links

Links is a small-footprint system for producing **verifiable, inspectable claim bundles** and exchanging them between nodes with **group policy controls**.

## What you get

- **Claim bundles**: portable JSON artifacts with explicit claims + signature integrity
- **Local store**: filesystem-backed storage of verified bundles + flattened index for querying
- **Villages**: groups with membership, access control, and policy norms for acceptance
- **Quarantine**: a review workflow for policy failures
- **Audit log**: append-only operational trace of decisions

## Install

```bash
pip install -e .
```

## Run a node

```bash
links serve --host 127.0.0.1 --port 8080
```

### TLS and deployment posture

Bearer tokens are credentials. For any non-local deployment, run this service **behind TLS** (reverse proxy / ingress) and treat logs as sensitive.

## Villages

Create a village:

```bash
links villages create ops "Ops Village" alice
```

The command prints an **admin bearer token once**. Store it securely.

Push to a village inbox:

```bash
links sync push-village http://127.0.0.1:8080 ops <TOKEN> --bundle artifacts/claims/claim_bundle.signed.json
```

Pull the latest village bundle:

```bash
links sync pull-village http://127.0.0.1:8080 ops <TOKEN>
```

## Quarantine review

```bash
links quarantine list --village-id ops
links quarantine approve data/store/quarantine/ops/<BUNDLE_ID>.json
links quarantine reject data/store/quarantine/ops/<BUNDLE_ID>.json --reason "policy mismatch"
```

Approvals re-check current village policy before ingestion.

## Documentation

- `docs/ethics.md`
- `docs/risks.md`
- ``


## Policy feed and reconciliation

Nodes can publish village policy updates and other nodes can **pull**, verify, reconcile, and apply them.

### Policy feed endpoints

- `GET /villages/{village_id}/policy/latest`
- `GET /villages/{village_id}/policy/updates?since=<policy_hash>`
- `POST /villages/{village_id}/policy` (stores an update; may be admin-gated depending on local village configuration)

### Pull + apply (client)

```bash
links policy pull http://127.0.0.1:8080 ops --apply
```

### Drift detection

```bash
links policy drift http://127.0.0.1:8080 ops
```

Reconciliation rule: select the most recent update by `(created_at, policy_hash)`.


### M-of-N signer quorum for policy updates

Villages can require a signer quorum for policy updates:

- `require_policy_signature: true`
- `policy_signature_threshold_m: <M>`
- `policy_signer_allowlist: [<key-hash-1>, <key-hash-2>, ...]`

A policy update is accepted only if at least **M distinct allowlisted signers** have produced valid signatures over the update payload.

#### Creating a multisig policy update artifact

Generate an unsigned update, then have multiple operators append signatures:

```bash
# signer A
links policy sign-add artifacts/policy_update.json keys/policy/alice.key artifacts/policy_update.s1.json

# signer B (appends on top)
links policy sign-add artifacts/policy_update.s1.json keys/policy/bob.key artifacts/policy_update.s2.json
```

Verify:
```bash
links policy verify artifacts/policy_update.s2.json
```

### Governance upgrades (policy evolution)

- Quorum models: **M-of-N**, **weighted signers**, and **role-based quorum sets**
- Policy lifecycle: proposal → approval → activation (with activation time/height)
- Policy versioning and deterministic rollback by prior policy hash
- Signed policy feed manifests + pagination for large histories
- Trust anchor registry (register / rotate / revoke) as signed artifacts

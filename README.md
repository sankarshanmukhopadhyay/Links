# Links

Links is a small-footprint system for producing **verifiable, inspectable claim bundles** from observable signals and exchanging them between nodes with **group policy controls**.

The design goal is practical: produce artifacts that can be shared, validated, and governed without turning the system into a black box.

## Core concepts

- **Claim bundle**: a portable JSON artifact containing explicit claims plus cryptographic integrity (signature) and stable identifiers.
- **Store**: a local filesystem-backed store of verified bundles and a flattened index for querying.
- **Villages**: groups that define membership, access control, and policy norms for what claims are accepted.

## Install

```bash
pip install -e .
```

## Run a local exchange node

```bash
links serve --host 127.0.0.1 --port 8080
```

## Villages: governance + enforcement

Villages give you a policy perimeter. You define who can push/pull, which predicates are acceptable, and which issuers are trusted.

### Create a village

```bash
links villages create ops "Ops Village" alice
```

The command prints an **admin bearer token once**. Store it securely.

### Add a member

```bash
links villages add-member ops bob --role member
```

### Revoke or rotate a member token

```bash
links villages revoke-member ops bob
links villages rotate-token ops bob
```

### Issuer trust controls

Villages can allowlist or blocklist issuer public keys. The control uses a key hash derived from the bundle `public_key`.

```bash
# Allow an issuer public key (base64 string)
links villages allow-issuer ops "<PUBLIC_KEY_B64>"

# Block an issuer public key
links villages block-issuer ops "<PUBLIC_KEY_B64>"
```

If a village is configured with `require_issuer_allowlist=true`, only allowlisted issuers will be accepted.

## Exchange bundles with village controls

### Push into a village inbox

```bash
links sync push-village http://127.0.0.1:8080 ops <TOKEN> --bundle artifacts/claims/claim_bundle.signed.json
```

### Pull the latest village bundle

```bash
links sync pull-village http://127.0.0.1:8080 ops <TOKEN>
```

## Quarantine and review workflow

Bundles that fail policy checks can be quarantined for review rather than silently dropped.

```bash
links quarantine list --village-id ops
links quarantine approve data/store/quarantine/ops/<BUNDLE_ID>.json
links quarantine reject data/store/quarantine/ops/<BUNDLE_ID>.json --reason "policy mismatch"
```

## Ethical safeguards and risk register

- `docs/ethics.md`
- `docs/risks.md`

These docs are part of the deliverable: if you deploy this system, treat them as operational requirements, not optional reading.

## API endpoints

- `GET /.well-known/links/claims/latest`
- `GET /villages/{village_id}/claims/latest` (Bearer token required)
- `POST /inbox`
- `POST /villages/{village_id}/inbox` (Bearer token + policy enforcement)


## Policy updates

Village policies can be updated through an admin-gated API endpoint. Updates can be provided as plain policy objects or as signed policy update artifacts.

### Update policy remotely (admin token required)

```bash
links policy export ops --out artifacts/policy_update.json
links policy apply-remote http://127.0.0.1:8080 ops <ADMIN_TOKEN> artifacts/policy_update.json
```

### Signed policy updates (recommended for stronger governance)

```bash
links policy gen-key --out-dir keys/policy
links policy export ops --out artifacts/policy_update.json
links policy sign --in artifacts/policy_update.json --key keys/policy/ed25519.key --out artifacts/policy_update.signed.json
links policy verify --in artifacts/policy_update.signed.json
links policy apply-remote http://127.0.0.1:8080 ops <ADMIN_TOKEN> artifacts/policy_update.signed.json
```

If a village is configured with `require_policy_signature=true`, the server will require a valid signature and can restrict which policy signers are permitted via `policy_signer_allowlist`.

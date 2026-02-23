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
- `docs/NEXT_INCREMENT_PLAN.md`

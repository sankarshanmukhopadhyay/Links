# Single-node dev profile

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
export LINKS_NODE_SIGNING_KEY_B64="$(python -c 'import base64; from nacl.signing import SigningKey; print(base64.b64encode(SigningKey.generate()._seed).decode())')"
links serve --host 127.0.0.1 --port 8000
```

## Notes
- Default storage backend is filesystem under `data/`.
- For local testing you can enable the public policy endpoint:
  `export LINKS_PUBLIC_POLICY=1`

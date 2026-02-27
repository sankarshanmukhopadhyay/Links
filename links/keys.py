from __future__ import annotations

import base64
from pathlib import Path
from nacl.signing import SigningKey


def generate_ed25519_keypair(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sk = SigningKey.generate()
    seed = sk._seed
    pub = sk.verify_key.encode()

    priv_path = out_dir / "ed25519.key"
    pub_path = out_dir / "ed25519.pub"

    priv_path.write_text(base64.b64encode(seed).decode("utf-8") + "\n", encoding="utf-8")
    pub_path.write_text(base64.b64encode(pub).decode("utf-8") + "\n", encoding="utf-8")
    return priv_path, pub_path


def load_signing_key_from_env(env_var: str = "LINKS_NODE_SIGNING_KEY_B64") -> SigningKey:
    """Load an Ed25519 SigningKey from a base64-encoded 32-byte seed in an environment variable."""
    import os
    v = os.environ.get(env_var, "").strip()
    if not v:
        raise ValueError(f"Missing {env_var} (base64-encoded 32-byte Ed25519 seed)")
    raw = base64.b64decode(v, validate=True)
    if len(raw) != 32:
        raise ValueError(f"{env_var} must decode to 32 bytes (got {len(raw)})")
    return SigningKey(raw)

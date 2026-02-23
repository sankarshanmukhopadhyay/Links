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

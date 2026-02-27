from __future__ import annotations

import base64
from typing import Literal, Tuple

from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


Alg = Literal["ed25519", "ecdsa_p256"]


def sign_bytes(payload: bytes, *, alg: Alg, signing_key_b64: str) -> str:
    """Return base64 signature."""
    if alg == "ed25519":
        sk = SigningKey(base64.b64decode(signing_key_b64, validate=True))
        sig = sk.sign(payload).signature
        return base64.b64encode(sig).decode("utf-8")
    if alg == "ecdsa_p256":
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec
        except Exception as e:  # pragma: no cover
            raise RuntimeError("cryptography required for ecdsa_p256") from e
        priv = serialization.load_pem_private_key(base64.b64decode(signing_key_b64, validate=True), password=None)
        if not isinstance(priv, ec.EllipticCurvePrivateKey):
            raise ValueError("Not an EC private key")
        sig = priv.sign(payload, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(sig).decode("utf-8")
    raise ValueError(f"Unsupported alg: {alg}")


def verify_bytes(payload: bytes, *, alg: Alg, public_key_b64: str, signature_b64: str) -> bool:
    if alg == "ed25519":
        try:
            vk = VerifyKey(base64.b64decode(public_key_b64, validate=True))
            vk.verify(payload, base64.b64decode(signature_b64, validate=True))
            return True
        except (BadSignatureError, Exception):
            return False
    if alg == "ecdsa_p256":
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.exceptions import InvalidSignature
        except Exception:
            return False
        try:
            pub = serialization.load_pem_public_key(base64.b64decode(public_key_b64, validate=True))
            if not isinstance(pub, ec.EllipticCurvePublicKey):
                return False
            pub.verify(base64.b64decode(signature_b64, validate=True), payload, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, Exception):
            return False
    return False

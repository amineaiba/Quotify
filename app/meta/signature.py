import hashlib
import hmac

_PREFIX = "sha256="


def verify_signature(raw_body: bytes, header_sig: str | None, app_secret: str) -> bool:
    """Constant-time check that raw_body was signed with app_secret (Meta's X-Hub-Signature-256)."""
    if header_sig is None or not header_sig.startswith(_PREFIX):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_sig[len(_PREFIX) :])

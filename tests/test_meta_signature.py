import hashlib
import hmac

from app.meta.signature import verify_signature

SECRET = "test-secret"
BODY = b'{"hello":"world"}'


def _sign(body: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_signature_accepts_correct_signature():
    assert verify_signature(BODY, _sign(BODY), SECRET) is True


def test_verify_signature_rejects_changed_body():
    assert verify_signature(b'{"hello":"tampered"}', _sign(BODY), SECRET) is False


def test_verify_signature_rejects_wrong_secret():
    assert verify_signature(BODY, _sign(BODY, "other-secret"), SECRET) is False


def test_verify_signature_rejects_missing_header():
    assert verify_signature(BODY, None, SECRET) is False


def test_verify_signature_rejects_malformed_header():
    assert verify_signature(BODY, "not-a-real-signature", SECRET) is False

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip_and_salt():
    first, second = hash_password("secreto"), hash_password("secreto")
    assert first != second  # sal aleatoria
    assert verify_password("secreto", first)
    assert not verify_password("otro", first)


def test_verify_password_handles_missing_or_malformed_hashes():
    assert not verify_password("x", None)
    assert not verify_password("x", "")
    assert not verify_password("x", "md5$abc")
    assert not verify_password("x", "scrypt$zz$00")


def test_token_roundtrip():
    assert decode_access_token(create_access_token(42)) == 42


def test_expired_or_tampered_tokens_are_rejected():
    assert decode_access_token(create_access_token(42, expires_minutes=-1)) is None
    token = create_access_token(42)
    assert decode_access_token(token[:-2] + ("A" if token[-1] != "A" else "B") + "x") is None
    assert decode_access_token("basura") is None

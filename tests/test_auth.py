import pytest
from app.auth import hash_password, verify_password, create_token, decode_token


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("testpassword")
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_token(1, "testuser")
        payload = decode_token(token)
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        with pytest.raises(Exception):
            decode_token("invalid.token.here")

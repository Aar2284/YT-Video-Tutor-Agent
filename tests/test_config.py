import pytest
from app.config import GROQ_MODEL, JWT_ALGORITHM, JWT_EXPIRY_HOURS


class TestConfig:
    def test_groq_model_is_set(self):
        assert GROQ_MODEL is not None
        assert isinstance(GROQ_MODEL, str)

    def test_jwt_algorithm(self):
        assert JWT_ALGORITHM == "HS256"

    def test_jwt_expiry_hours(self):
        assert JWT_EXPIRY_HOURS > 0
        assert isinstance(JWT_EXPIRY_HOURS, int)

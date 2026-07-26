import sys
import os
import pytest

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def anyio_backend():
    return "asyncio"

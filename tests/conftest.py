"""Pytest configuration and test fixtures."""
import pytest
from src.main import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

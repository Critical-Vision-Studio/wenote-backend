"""Test configuration constants."""
from pathlib import Path

# Constants for test configuration
TEST_REPO_NAME = "test_repo"

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# Test settings
TEST_SETTINGS = {
    'TESTING': True,
    'DEBUG': True
} 
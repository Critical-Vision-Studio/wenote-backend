import os
import tempfile
import pytest
from app import create_app
from app.utils import GitCommander
from config import settings
from unittest import mock

@pytest.fixture
def client():
    """Flask test client fixture."""
    app = create_app()
    app.config["TESTING"] = True
    
    with app.app_context():
        with app.test_client() as client:
            yield client

@pytest.fixture
def temp_dir():
    """Temporary directory fixture for Git operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def temp_repo(temp_dir):
    """Initialized Git repository fixture."""
    gc = GitCommander(temp_dir)
    gc.create_repo()
    settings.REPO_PATH = temp_dir
    yield temp_dir

@pytest.fixture
def mock_git_commander():
    """Mock GitCommander fixture for route testing."""
    with mock.patch('app.utils.GitCommander') as mock_gc:
        # Configure common mock methods
        mock_gc.return_value.list_branches.return_value = ['master']
        mock_gc.return_value.branch_exists.return_value = True
        mock_gc.return_value.get_commit_id.return_value = 'mock-commit-id'
        yield mock_gc 
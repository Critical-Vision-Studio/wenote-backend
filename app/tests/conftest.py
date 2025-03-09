"""Test fixtures and configuration."""
import pytest
import tempfile
import subprocess
from pathlib import Path
from app import create_app
from app.utils import GitCommander
from unittest import mock
from .test_config import TEST_REPO_NAME

@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for tests.
    
    This fixture creates an actual Git repository in a temporary directory,
    configures it with test user details, and cleans up after the test.
    
    Returns:
        str: Path to the temporary repository
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize Git repository
        gc = GitCommander(temp_dir)
        gc.create_repo()
        
        # Configure Git user for the repository
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
        
        yield temp_dir
        # Directory and its contents are automatically cleaned up after the test

@pytest.fixture
def client():
    """Flask test client fixture."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_services():
    """Mock all service functions for unit tests."""
    with mock.patch('app.routes.note_routes.get_note') as mock_get_note, \
         mock.patch('app.routes.note_routes.get_note_names') as mock_get_names, \
         mock.patch('app.routes.note_routes.create_note') as mock_create, \
         mock.patch('app.routes.note_routes.update_note') as mock_update, \
         mock.patch('app.routes.note_routes.delete_note') as mock_delete:
        
        # Configure default returns
        mock_get_note.return_value = {"note": "Test content", "readonly": False}
        mock_get_names.return_value = {"notes": ["note1.txt", "note2.txt"], "branch_name": "master"}
        mock_create.return_value = {"status": 201, "message": "created"}
        mock_update.return_value = ("ok", "Updated content", "master", "new-commit-id")
        mock_delete.return_value = ("ok", None)
        
        yield {
            'get_note': mock_get_note,
            'get_note_names': mock_get_names,
            'create_note': mock_create,
            'update_note': mock_update,
            'delete_note': mock_delete
        } 
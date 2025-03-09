import pytest
from unittest import mock
import os

def test_get_note(client, mock_services, test_repo_path):
    """Test get_note route."""
    response = client.get(f"/apiv1/get-note?repo_path={test_repo_path}&note_path=test.txt&branch_name=master")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["note"] == "Test content"
    assert not data["readonly"]
    
    mock_services['get_note'].assert_called_once_with(str(test_repo_path), "test.txt", "master")

def test_get_note_names(client, mock_services, test_repo_path):
    """Test get_note_names route."""
    response = client.get(f"/apiv1/get-note-names?repo_path={test_repo_path}&branch_name=master")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["notes"] == ["note1.txt", "note2.txt"]
    assert data["branch_name"] == "master"
    
    mock_services['get_note_names'].assert_called_once_with(str(test_repo_path), "master")

def test_create_note_route(client, mock_services, test_repo_path):
    """Test create_note route."""
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": str(test_repo_path),
            "note_path": "test.txt",
            "note_value": "Test content"
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == 201
    assert data["message"] == "created"
    
    mock_services['create_note'].assert_called_once_with(str(test_repo_path), "test.txt", "Test content")

def test_update_note_route(client, mock_services, test_repo_path):
    """Test update_note route."""
    response = client.put(
        "/apiv1/update-note",
        json={
            "repo_path": str(test_repo_path),
            "note_path": "test.txt",
            "note_value": "Updated content",
            "branch_name": "master",
            "commit_id": "test-commit-id"
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["note"] == "Updated content"
    assert data["branch_name"] == "master"
    assert data["commit_id"] == "new-commit-id"
    
    mock_services['update_note'].assert_called_once_with(
        str(test_repo_path), "master", "test-commit-id", "test.txt", "Updated content"
    )

def test_delete_note_route(client, mock_services, test_repo_path):
    """Test delete_note route."""
    response = client.delete(
        "/apiv1/delete-note",
        json={
            "repo_path": str(test_repo_path),
            "note_path": "test.txt",
            "branch_name": "master"
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["note_value"] is None
    
    mock_services['delete_note'].assert_called_once_with(str(test_repo_path), "test.txt", "master")

def test_create_note_route_errors(client, mock_services, test_repo_path):
    """Test error handling in create_note route."""
    # Test duplicate note
    mock_services['create_note'].return_value = {"status": "error", "message": "conflict"}
    
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": str(test_repo_path),
            "note_path": "existing.txt",
            "note_value": "test"
        }
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "conflict"

##### ERROR HANDLING TESTS #####

def test_get_note_route_errors(client, mock_services):
    """Test error handling in get_note route."""
    # Test non-existent note
    mock_services['get_note'].return_value = None
    response = client.get("/apiv1/get-note?repo_path=/mock/repo&note_path=nonexistent.txt&branch_name=master")
    assert response.status_code == 400
    
    # Test non-existent branch
    mock_services['get_note'].side_effect = Exception("Branch not found")
    response = client.get("/apiv1/get-note?repo_path=/mock/repo&note_path=test.txt&branch_name=nonexistent")
    assert response.status_code == 400

##### VALIDATION TESTS #####

@pytest.mark.parametrize("path", [
    "../test.txt",
    "../../test.txt",
    "/etc/passwd",
    "test/../../etc/passwd",
])
def test_path_traversal_prevention(client, mock_services, path):
    """Test path traversal prevention in routes."""
    response = client.get(f"/apiv1/get-note?repo_path=/mock/repo&note_path={path}&branch_name=master")
    assert response.status_code == 400
    assert "error" in response.get_json()

@pytest.mark.parametrize("input_data", [
    {},  # Empty data
    {"repo_path": "/mock/repo"},  # Missing fields
    {"repo_path": "/mock/repo", "note_path": "", "note_value": "test"},  # Empty path
    {"repo_path": "/mock/repo", "note_path": "test.txt", "note_value": ""},  # Empty content
])
def test_input_validation(client, mock_services, input_data):
    """Test input validation in routes."""
    response = client.post("/apiv1/create-note", json=input_data)
    assert response.status_code == 400
    assert "error" in response.get_json() 
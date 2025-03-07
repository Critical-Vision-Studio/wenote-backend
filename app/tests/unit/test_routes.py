import pytest
from unittest import mock

def test_get_note_route(client, mock_git_commander):
    """Test get_note route with mocked GitCommander."""
    mock_instance = mock_git_commander.return_value
    mock_instance.file_exists.return_value = True
    mock_instance.show_file.return_value = "Test content"
    
    response = client.get("/apiv1/get-note?repo_path=/mock/repo&note_path=test.txt&branch_name=master")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["note"] == "Test content"
    assert not data["readonly"]  # Default value
    
    # Verify correct GitCommander usage
    mock_instance.file_exists.assert_called_once_with("test.txt", "master")
    mock_instance.show_file.assert_called_once_with("test.txt", "master")

def test_get_note_names_route(client, mock_git_commander):
    """Test get_note_names route with mocked GitCommander."""
    mock_instance = mock_git_commander.return_value
    mock_instance.list_files.return_value = ["note1.txt", "note2.txt"]
    
    response = client.get("/apiv1/get-note-names?repo_path=/mock/repo&branch_name=master")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["notes"] == ["note1.txt", "note2.txt"]
    assert data["branch_name"] == "master"
    
    mock_instance.list_files.assert_called_once_with("master")

def test_create_note_route(client, mock_git_commander):
    """Test create_note route with mocked GitCommander."""
    mock_instance = mock_git_commander.return_value
    mock_instance.branch_exists.return_value = False
    mock_instance.merge.return_value = False
    
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": "test.txt",
            "note_value": "Test content"
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == 201
    assert data["message"] == "created"
    
    # Verify correct sequence of Git operations
    mock_instance.create_branch.assert_called_once()
    mock_instance.write_note.assert_called_once_with("test.txt", "Test content")
    mock_instance.add_file.assert_called_once_with("test.txt")
    mock_instance.commit.assert_called_once()
    mock_instance.merge.assert_called()

def test_update_note_route(client, mock_git_commander):
    """Test update_note route with mocked GitCommander."""
    mock_instance = mock_git_commander.return_value
    mock_instance.merge.return_value = False
    
    response = client.put(
        "/apiv1/update-note",
        json={
            "repo_path": "/mock/repo",
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
    
    # Verify Git operations
    mock_instance.write_note.assert_called_once_with("test.txt", "Updated content")
    mock_instance.add_file.assert_called_once_with("test.txt")
    mock_instance.commit.assert_called_once()

def test_delete_note_route(client, mock_git_commander):
    """Test delete_note route with mocked GitCommander."""
    mock_instance = mock_git_commander.return_value
    mock_instance.merge.return_value = False
    mock_instance.file_exists.return_value = True
    
    response = client.delete(
        "/apiv1/delete-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": "test.txt",
            "branch_name": "master"
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    
    # Verify Git operations
    mock_instance.file_exists.assert_called_once_with("test.txt", "master")
    mock_instance.delete_file.assert_called_once_with("test.txt")
    mock_instance.commit.assert_called_once()

##### ERROR HANDLING TESTS #####

def test_get_note_route_errors(client, mock_git_commander):
    """Test error handling in get_note route."""
    mock_instance = mock_git_commander.return_value
    
    # Test non-existent note
    mock_instance.file_exists.return_value = False
    response = client.get("/apiv1/get-note?repo_path=/mock/repo&note_path=nonexistent.txt&branch_name=master")
    assert response.status_code == 400
    
    # Test non-existent branch
    mock_instance.file_exists.side_effect = Exception("Branch not found")
    response = client.get("/apiv1/get-note?repo_path=/mock/repo&note_path=test.txt&branch_name=nonexistent")
    assert response.status_code == 400

def test_create_note_route_errors(client, mock_git_commander):
    """Test error handling in create_note route."""
    mock_instance = mock_git_commander.return_value
    
    # Test duplicate note
    mock_instance.branch_exists.return_value = True
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": "existing.txt",
            "note_value": "test"
        }
    )
    assert response.status_code == 400
    
    # Test merge conflict
    mock_instance.branch_exists.return_value = False
    mock_instance.merge.return_value = True  # Indicates conflict
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": "conflict.txt",
            "note_value": "test"
        }
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "conflict"

##### VALIDATION TESTS #####

@pytest.mark.parametrize("path", [
    "../test.txt",
    "../../test.txt",
    "/etc/passwd",
    "test/../../etc/passwd",
])
def test_path_traversal_prevention(client, mock_git_commander, path):
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
def test_input_validation(client, mock_git_commander, input_data):
    """Test input validation in routes."""
    response = client.post("/apiv1/create-note", json=input_data)
    assert response.status_code == 400
    assert "error" in response.get_json() 
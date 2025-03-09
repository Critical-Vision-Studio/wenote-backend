import pytest
from unittest import mock

@pytest.mark.parametrize("path", [
    "../test.txt",
    "../../test.txt",
    "/etc/passwd",
    "test/../../etc/passwd",
    "..\\test.txt",
    "..\\..\\test.txt",
    "C:\\Windows\\System32\\test.txt"
])
def test_path_traversal_prevention(client, mock_services, path):
    """Test path traversal prevention in routes."""
    response = client.get(f"/apiv1/get-note?repo_path=/mock/repo&note_path={path}&branch_name=master")
    assert response.status_code == 400
    assert "error" in response.get_json()
    
    # Test create-note
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": path,
            "note_value": "test"
        }
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
    
    # Test update-note
    response = client.put(
        "/apiv1/update-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": path,
            "note_value": "test",
            "branch_name": "master",
            "commit_id": "test-id"
        }
    )
    assert response.status_code == 400
    assert "error" in response.get_json()

@pytest.mark.parametrize("name", [
    "test; rm -rf /",
    "test && rm -rf /",
    "test | rm -rf /",
    "test`rm -rf /`",
    "test$(rm -rf /)",
    "test\nrm -rf /",
    "test\rrm -rf /",
    "test\trm -rf /",
    "test\\rm -rf /",
    "test/../rm -rf /"
])
def test_malicious_file_names(client, mock_services, name):
    """Test prevention of malicious file names."""
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": name,
            "note_value": "test"
        }
    )
    assert response.status_code == 400
    assert "error" in response.get_json()

@pytest.mark.parametrize("system_file", [
    ".git",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini"
])
def test_system_files(client, mock_services, system_file):
    """Test prevention of accessing system files."""
    response = client.get(f"/apiv1/get-note?repo_path=/mock/repo&note_path={system_file}&branch_name=master")
    assert response.status_code == 400
    assert "error" in response.get_json()

@pytest.mark.parametrize("endpoint,params", [
    ("/apiv1/get-note", {"note_path": "", "branch_name": "master"}),
    ("/apiv1/get-note", {"note_path": "test.txt", "branch_name": ""}),
    ("/apiv1/get-note-names", {"branch_name": ""}),
    ("/apiv1/create-note", {"note_path": "", "note_value": "test"}),
    ("/apiv1/create-note", {"note_path": "test.txt", "note_value": ""}),
])
def test_empty_inputs(client, mock_services, endpoint, params):
    """Test handling of empty inputs."""
    response = client.get(endpoint, query_string=params) if endpoint.startswith("/apiv1/get") else \
               client.post(endpoint, json=params)
    assert response.status_code == 400
    assert "error" in response.get_json() 
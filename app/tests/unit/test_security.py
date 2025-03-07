import pytest

@pytest.mark.parametrize("path", [
    "../test.txt",
    "../../test.txt",
    "/etc/passwd",
    "test/../../etc/passwd",
    "..\\test.txt",
    "..\\..\\test.txt",
    "C:\\Windows\\System32\\test.txt"
])
def test_path_traversal_prevention(client, mock_git_commander, path):
    """Test prevention of path traversal attacks."""
    # Test get-note
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
def test_malicious_file_names(client, mock_git_commander, name):
    """Test prevention of command injection through file names."""
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
def test_system_files(client, mock_git_commander, system_file):
    """Test prevention of access to system files."""
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": "/mock/repo",
            "note_path": system_file,
            "note_value": "test"
        }
    )
    assert response.status_code == 400
    assert "error" in response.get_json()

@pytest.mark.parametrize("endpoint,params", [
    ("/apiv1/get-note", {"note_path": "", "branch_name": "master"}),
    ("/apiv1/get-note", {"note_path": "test.txt", "branch_name": ""}),
    ("/apiv1/get-note-names", {"branch_name": ""}),
    ("/apiv1/create-note", {"note_path": "", "note_value": "test"}),
    ("/apiv1/create-note", {"note_path": "test.txt", "note_value": ""}),
])
def test_empty_inputs(client, mock_git_commander, endpoint, params):
    """Test handling of empty or missing required fields."""
    if endpoint in ["/apiv1/get-note", "/apiv1/get-note-names"]:
        params["repo_path"] = "/mock/repo"
        response = client.get(endpoint, query_string=params)
    else:
        response = client.post(endpoint, json=params)
    
    assert response.status_code == 400
    assert "error" in response.get_json() 
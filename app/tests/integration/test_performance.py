import os
import concurrent.futures
import time
import string
import random
from app.utils import GitCommander

def test_large_file_handling(client, temp_repo):
    """Test handling of large number of files."""
    TEST_FILE_COUNT = 50  # Reduced from original for reasonable test duration
    
    # Create multiple files
    for i in range(TEST_FILE_COUNT):
        file_name = f"test_file_{i}.txt"
        content = f"Content for file {i}"
        commander = GitCommander(temp_repo)
        commander.write_note(file_name, content)
        commander.add_file(file_name)
        commander.commit(f"Add {file_name}")
    
    # Test listing files
    response = client.get(f"/apiv1/get-note-names?repo_path={temp_repo}&branch_name=master")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["notes"]) >= TEST_FILE_COUNT

def test_concurrent_access(client, temp_repo):
    """Test concurrent access to the repository."""
    TEST_ITERATIONS = 10
    file_name = "concurrent_test.txt"
    
    def update_note(i):
        response = client.put(
            "/apiv1/update-note",
            json={
                "repo_path": temp_repo,
                "note_path": file_name,
                "note_value": f"Update {i}",
                "branch_name": "master",
                "commit_id": GitCommander(temp_repo).get_commit_id("master")
            }
        )
        return response.status_code
    
    # Create initial file
    commander = GitCommander(temp_repo)
    commander.write_note(file_name, "Initial content")
    commander.add_file(file_name)
    commander.commit("Initial commit")
    
    # Perform concurrent updates
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(update_note, range(TEST_ITERATIONS)))
    
    # Verify all operations completed
    assert all(status == 200 for status in results)
    
    # Verify final state
    response = client.get(f"/apiv1/get-note?repo_path={temp_repo}&note_path={file_name}&branch_name=master")
    assert response.status_code == 200

def test_special_characters(client, temp_repo):
    """Test handling of special characters in file names and content."""
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>? "
    unicode_chars = "你好世界¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶"
    
    # Test file name with special characters
    file_name = f"test{special_chars}.txt"
    content = f"Content with {unicode_chars}"
    
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": temp_repo,
            "note_path": file_name,
            "note_value": content
        }
    )
    assert response.status_code == 200
    
    # Verify content
    response = client.get(f"/apiv1/get-note?repo_path={temp_repo}&note_path={file_name}&branch_name=master")
    assert response.status_code == 200
    assert response.get_json()["note"] == content

def test_long_paths(client, temp_repo):
    """Test handling of very long file paths."""
    # Create a deep directory structure
    long_path = "a/b/c/d/e/f/g/h/i/j/k/l/m/n/o/p/test.txt"
    content = "Test content"
    
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": temp_repo,
            "note_path": long_path,
            "note_value": content
        }
    )
    assert response.status_code == 200
    
    # Verify content
    response = client.get(f"/apiv1/get-note?repo_path={temp_repo}&note_path={long_path}&branch_name=master")
    assert response.status_code == 200
    assert response.get_json()["note"] == content 
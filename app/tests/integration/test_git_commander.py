import os
import tempfile
import pytest
from app.utils import GitCommander

def test_git_commander_initialization(temp_repo):
    """Test GitCommander initialization with a real repository."""
    commander = GitCommander(temp_repo)
    assert os.path.exists(os.path.join(temp_repo, ".git"))

def test_create_and_show_file(temp_repo):
    """Test creating and showing a file in the repository."""
    commander = GitCommander(temp_repo)
    test_content = "Test content\nLine 2"
    
    # Create and commit a file
    commander.write_note("test.txt", test_content)
    commander.add_file("test.txt")
    commander.commit(msg="Add test.txt")
    
    # Verify file exists and content matches
    assert commander.file_exists("test.txt", "master")
    content = commander.show_file("test.txt", "master")
    assert content == test_content

def test_branch_operations(temp_repo):
    """Test branch creation, switching, and merging."""
    commander = GitCommander(temp_repo)
    
    # Create initial file in master
    commander.write_note("master.txt", "Master content")
    commander.add_file("master.txt")
    commander.commit(msg="Add master.txt")
    
    # Create and switch to new branch
    new_branch = "feature-branch"
    commander.create_branch(new_branch)
    
    # Add file in new branch
    commander.write_note("feature.txt", "Feature content")
    commander.add_file("feature.txt")
    commander.commit(msg="Add feature.txt")
    
    # Verify branch exists and files are correct
    assert commander.branch_exists(new_branch)
    assert commander.file_exists("feature.txt", new_branch)
    assert commander.file_exists("master.txt", new_branch)
    
    # Test merging
    has_conflict = commander.merge(new_branch)
    assert not has_conflict
    assert commander.file_exists("feature.txt", "master")

def test_merge_conflict_handling(temp_repo):
    """Test handling of merge conflicts."""
    commander = GitCommander(temp_repo)
    
    # Create file in master
    commander.write_note("conflict.txt", "Master content")
    commander.add_file("conflict.txt")
    commander.commit(msg="Add conflict.txt in master")
    
    # Create branch and modify same file
    commander.create_branch("feature")
    commander.write_note("conflict.txt", "Feature content")
    commander.add_file("conflict.txt")
    commander.commit(msg="Modify conflict.txt in feature")
    
    # Modify file in master to create conflict
    commander.checkout_branch("master")
    commander.write_note("conflict.txt", "Updated master content")
    commander.add_file("conflict.txt")
    commander.commit(msg="Update conflict.txt in master")
    
    # Attempt merge and verify conflict is detected
    has_conflict = commander.merge("feature")
    assert has_conflict

def test_file_operations(temp_repo):
    """Test various file operations."""
    commander = GitCommander(temp_repo)
    
    # Test file creation and listing
    commander.write_note("note1.txt", "Content 1")
    commander.write_note("note2.txt", "Content 2")
    commander.add_file("note1.txt")
    commander.add_file("note2.txt")
    commander.commit(msg="Add test notes")
    
    files = commander.list_files("master")
    assert "note1.txt" in files
    assert "note2.txt" in files
    
    # Test file deletion
    commander.delete_file("note1.txt")
    commander.commit(msg="Delete note1.txt")
    
    files = commander.list_files("master")
    assert "note1.txt" not in files
    assert "note2.txt" in files
    
    # Test file existence checks
    assert not commander.file_exists("note1.txt", "master")
    assert commander.file_exists("note2.txt", "master")

def test_commit_history(temp_repo):
    """Test commit history related operations."""
    commander = GitCommander(temp_repo)
    
    # Create multiple commits
    commander.write_note("test.txt", "Initial content")
    commander.add_file("test.txt")
    commander.commit(msg="Initial commit")
    
    commander.write_note("test.txt", "Updated content")
    commander.add_file("test.txt")
    commander.commit(msg="Update content")
    
    # Test getting file from specific commit
    commits = commander.get_commits("test.txt")
    assert len(commits) >= 2
    
    # Verify content at different commits
    first_commit = commits[-1]
    latest_commit = commits[0]
    
    content = commander.show_file("test.txt", commit_id=first_commit)
    assert content == "Initial content"
    
    content = commander.show_file("test.txt", commit_id=latest_commit)
    assert content == "Updated content"

@pytest.mark.parametrize("invalid_path", [
    "../test.txt",
    "../../test.txt",
    "/etc/passwd",
    "test/../../etc/passwd",
])
def test_path_validation(temp_repo, invalid_path):
    """Test path validation in GitCommander."""
    commander = GitCommander(temp_repo)
    
    with pytest.raises(ValueError):
        commander.write_note(invalid_path, "test content")
    
    with pytest.raises(ValueError):
        commander.show_file(invalid_path, "master")
    
    with pytest.raises(ValueError):
        commander.delete_file(invalid_path) 
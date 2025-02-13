import os
import tempfile
import pytest
import subprocess
from app.utils import GitCommander  # Assuming GitCommander is defined in app/utils.py

@pytest.fixture
def temp_git_repo():
    temp_dir = tempfile.mkdtemp()
    try:
        # Initialize a git repository and configure user details.
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
        yield temp_dir
    finally:
        import shutil
        shutil.rmtree(temp_dir)

@pytest.fixture
def git_commander(temp_git_repo):
    return GitCommander(temp_git_repo)

def test_create_repo(git_commander):
    # Even if the repo already exists, create_repo() should be safe to call.
    git_commander.create_repo()
    assert os.path.exists(os.path.join(git_commander.repo_path, ".git"))

def test_get_commit_id(git_commander):
    note_path = "test.txt"
    file_path = os.path.join(git_commander.repo_path, note_path)
    with open(file_path, "w") as f:
        f.write("Initial commit")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)

    commit_id = git_commander.get_commit_id("HEAD")
    # Verify that commit_id is a valid 40-character SHA-1 hash.
    assert len(commit_id) == 40

def test_file_exists(git_commander):
    branch_name = "master"
    note_path = "notes/note1.txt"
    full_dir = os.path.join(git_commander.repo_path, "notes")
    os.makedirs(full_dir, exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=git_commander.repo_path, check=True)

    assert git_commander.file_exists(note_path, branch_name)

def test_show_file(git_commander):
    branch_name = "master"
    note_path = "notes/note1.txt"
    note_value = "Test note"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write(note_value)
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=git_commander.repo_path, check=True)

    content = git_commander.show_file(note_path, branch_name)
    # Strip any trailing newline characters.
    assert content.strip() == note_value

def test_create_branch(git_commander):
    branch_name = "test-branch"
    git_commander.create_branch(branch_name)
    # Create a file and commit to record the branch.
    subprocess.run(["touch", "aaa"], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)

    output = subprocess.run(
        ["git", "branch", "-l", "--all"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    assert branch_name in output.stdout

def test_checkout_branch(git_commander):
    # Ensure that we have at least two branches.
    git_commander.create_branch("master")
    subprocess.run(["touch", "aaa"], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)

    branch_name = "test-branch"
    git_commander.create_branch(branch_name)
    git_commander.checkout_branch("master")
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    assert current_branch.stdout.strip() == "master"

def test_branch_exists(git_commander):
    branch_name = "test-branch"
    # Initially, the branch should not exist.
    assert not git_commander.branch_exists(branch_name)
    git_commander.create_branch(branch_name)
    subprocess.run(["touch", "aaa"], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)
    # Now the branch should exist.
    assert git_commander.branch_exists(branch_name)

def test_write_note(git_commander):
    note_path = "notes/note1.txt"
    note_value = "This is a test note"
    git_commander.write_note(note_path, note_value)
    with open(os.path.join(git_commander.repo_path, note_path), "r") as f:
        content = f.read()
    assert content == note_value

def test_add_file(git_commander):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("This is a test note")
    git_commander.add_file(note_path)
    output = subprocess.run(
        ["git", "status"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    assert "new file" in output.stdout and note_path in output.stdout

def test_commit(git_commander):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("This is a test note")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    git_commander.commit(note_path, "Add test note")
    log_output = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    assert "Add test note" in log_output.stdout

def test_merge(git_commander):
    # Prepare master branch.
    subprocess.run(["touch", "aaa"], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)

    branch_name = "test-branch"
    git_commander.create_branch(branch_name)
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=git_commander.repo_path, check=True)
    git_commander.checkout_branch("master")
    # Merge the test branch into master; expecting no conflict.
    assert not git_commander.merge(branch_name)

def test_delete_branch(git_commander):
    subprocess.run(["touch", "aaa"], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_commander.repo_path, check=True)

    branch_name = "test-branch"
    git_commander.create_branch(branch_name)
    git_commander.checkout_branch("master")
    git_commander.delete_branch(branch_name)
    output = subprocess.run(
        ["git", "branch"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    assert branch_name not in output.stdout

def test_delete_file(git_commander):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=git_commander.repo_path, check=True)
    git_commander.delete_file(note_path)
    output = subprocess.run(
        ["git", "status"],
        cwd=git_commander.repo_path,
        capture_output=True,
        text=True
    )
    # Check that Git status reflects the file removal.
    assert ("deleted:" in output.stdout or "deleted" in output.stdout) and note_path in output.stdout

def test_list_files(git_commander):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(git_commander.repo_path, "notes"), exist_ok=True)
    with open(os.path.join(git_commander.repo_path, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=git_commander.repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=git_commander.repo_path, check=True)
    files = git_commander.list_files("master")
    assert note_path in files

def test_get_current_branch(git_commander):
    current_branch = git_commander.get_current_branch()
    assert current_branch == "master"


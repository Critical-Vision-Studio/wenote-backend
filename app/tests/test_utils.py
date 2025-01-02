import os
import tempfile
import pytest
import subprocess
from app.utils import *

@pytest.fixture
def temp_git_repo():
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
        yield temp_dir
    finally:
        import shutil
        shutil.rmtree(temp_dir)


def test_create_repo(temp_git_repo):
    create_repo(temp_git_repo)
    assert os.path.exists(os.path.join(temp_git_repo, ".git"))


def test_get_commit_id(temp_git_repo):
    note_path = "test.txt"
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("Initial commit")
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_git_repo, check=True)

    commit_id = get_commit_id(temp_git_repo, "HEAD")
    assert len(commit_id) == 40  # A valid Git commit hash length


def test_file_exists(temp_git_repo):
    branch_name = "master"
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=temp_git_repo, check=True)

    assert file_exists(temp_git_repo, note_path, branch_name)


def test_show_file(temp_git_repo):
    branch_name = "master"
    note_path = "notes/note1.txt"
    note_value = "Test note"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write(note_value)
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=temp_git_repo, check=True)

    content = show_file(temp_git_repo, note_path, branch_name)
    assert content == note_value


def test_create_branch(temp_git_repo):
    branch_name = "test-branch"
    create_branch(temp_git_repo, branch_name)
    subprocess.run(["touch", "aaa"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "'Initial commit'"], cwd=temp_git_repo, check=True)

    output = subprocess.run(["git", "branch", "-l", "--all"], cwd=temp_git_repo, capture_output=True, text=True)

    print(output.stdout)
    assert branch_name in output.stdout


def test_checkout_branch(temp_git_repo):
    create_branch(temp_git_repo, "master")
    subprocess.run(["touch", "aaa"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "'Initial commit'"], cwd=temp_git_repo, check=True)

    branch_name = "test-branch"
    create_branch(temp_git_repo, branch_name)

    checkout_branch(temp_git_repo, "master")
    current_branch = subprocess.run(["git", "branch", "--show-current"], cwd=temp_git_repo, capture_output=True, text=True)
    assert current_branch.stdout.strip() == "master" 


def test_branch_exists(temp_git_repo):
    branch_name = "test-branch"
    assert not branch_exists(temp_git_repo, branch_name)
    create_branch(temp_git_repo, branch_name)

    subprocess.run(["touch", "aaa"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "'Initial commit'"], cwd=temp_git_repo, check=True)

    assert branch_exists(temp_git_repo, branch_name)


def test_write_note(temp_git_repo):
    note_path = "notes/note1.txt"
    note_value = "This is a test note"
    write_note(temp_git_repo, note_path, note_value)
    with open(os.path.join(temp_git_repo, note_path), "r") as f:
        content = f.read()
    assert content == note_value


def test_add_file(temp_git_repo):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("This is a test note")
    add_file(temp_git_repo, note_path)
    output = subprocess.run(["git", "status"], cwd=temp_git_repo, capture_output=True, text=True)
    assert "new file" in output.stdout and note_path in output.stdout


def test_commit(temp_git_repo):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("This is a test note")
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    commit(temp_git_repo, note_path, "Add test note")
    log_output = subprocess.run(["git", "log", "--oneline"], cwd=temp_git_repo, capture_output=True, text=True)
    assert "Add test note" in log_output.stdout


def test_merge(temp_git_repo):
    subprocess.run(["touch", "aaa"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "'Initial commit'"], cwd=temp_git_repo, check=True)

    branch_name = "test-branch"
    create_branch(temp_git_repo, branch_name)
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))

    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("Test note")

    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=temp_git_repo, check=True)
    checkout_branch(temp_git_repo, "master")
    assert not merge(temp_git_repo, branch_name)


def test_delete_branch(temp_git_repo):
    subprocess.run(["touch", "aaa"], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "'Initial commit'"], cwd=temp_git_repo, check=True)

    branch_name = "test-branch"
    create_branch(temp_git_repo, branch_name)
    checkout_branch(temp_git_repo, "master")

    delete_branch(temp_git_repo, branch_name)
    output = subprocess.run(["git", "branch"], cwd=temp_git_repo, capture_output=True, text=True)
    assert branch_name not in output.stdout


def test_delete_file(temp_git_repo):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=temp_git_repo, check=True)
    delete_file(temp_git_repo, note_path)
    output = subprocess.run(["git", "status"], cwd=temp_git_repo, capture_output=True, text=True)
    assert "deleted" in output.stdout and note_path in output.stdout


def test_list_files(temp_git_repo):
    note_path = "notes/note1.txt"
    os.makedirs(os.path.join(temp_git_repo, "notes"))
    with open(os.path.join(temp_git_repo, note_path), "w") as f:
        f.write("Test note")
    subprocess.run(["git", "add", note_path], cwd=temp_git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add test note"], cwd=temp_git_repo, check=True)
    files = list_files(temp_git_repo, "master")
    assert note_path in files


def test_get_current_branch(temp_git_repo):
    current_branch = get_current_branch(temp_git_repo)
    assert current_branch == "master"


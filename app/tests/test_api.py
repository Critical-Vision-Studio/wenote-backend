import os
import tempfile
import pytest
from app import create_app
from app.utils import GitCommander
from config import settings

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    
    with app.app_context():
        with app.test_client() as client:
            yield client

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as temp_dir:
        gc = GitCommander(temp_dir)
        gc.create_repo()
        print('in temp-repo', gc.list_branches())
        settings.REPO_PATH = temp_dir
        yield temp_dir


def add_file_to_repo(repo_path, file_name, content=""):
    gc = GitCommander(repo_path)
    gc.write_note(file_name, content)
    # Use GitCommander for adding and committing if desired;
    # here we continue to use os.system for brevity.
    os.system(f"git -C {repo_path} add {file_name}")
    os.system(f"git -C {repo_path} commit -m 'Add {file_name}'")


def test_get_note(client, temp_repo):
    file_name = "test_note.txt"
    branch_name = "master"
    gc = GitCommander(temp_repo)
    print(gc.list_branches())
    add_file_to_repo(temp_repo, file_name, "This is a test note.")

    response = client.get(f"/apiv1/get-note?repo_path={temp_repo}&note_path={file_name}&branch_name={branch_name}")
    assert response.status_code == 200
    data = response.get_json()
    assert "note" in data
    assert data["note"] == "This is a test note."


def test_get_note_names(client, temp_repo):
    branch_name = "master"
    file_names = [".gitkeep", "note1.txt", "note2.txt", "note3.txt"]
    gc = GitCommander(temp_repo)
    print(gc.list_branches())
    for file_name in file_names:
        add_file_to_repo(temp_repo, file_name, f"Content of {file_name}")

    response = client.get(f"/apiv1/get-note-names?repo_path={temp_repo}&branch_name={branch_name}")
    data = response.get_json()
    print(data)
    assert response.status_code == 200
    assert "notes" in data
    assert sorted(data["notes"]) == sorted(file_names)


def test_create_note(client, temp_repo):
    file_name = "new_note.txt"
    note_content = "This is a new note."
    gc = GitCommander(temp_repo)
    print(gc.list_branches())
    response = client.post(
        "/apiv1/create-note",
        json={"repo_path": temp_repo, "note_path": file_name, "note_value": note_content}
    )
    assert response.status_code == 200

    assert os.path.exists(os.path.join(temp_repo, file_name))
    with open(os.path.join(temp_repo, file_name), "r") as f:
        assert f.read() == note_content


def test_update_note(client, temp_repo):
    file_name = "existing_note.txt"
    initial_content = "This is the original content."
    updated_content = "This is the updated content."
    branch_name = "master"
    gc = GitCommander(temp_repo)

    add_file_to_repo(temp_repo, file_name, initial_content)
    commit_id = gc.get_commit_id(branch_name)

    response = client.put(
        "/apiv1/update-note",
        json={
            "repo_path": temp_repo,
            "note_path": file_name,
            "note_value": updated_content,
            "branch_name": branch_name,
            "commit_id": commit_id
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["note"] == updated_content


def test_delete_note(client, temp_repo):
    file_name = "note_to_delete.txt"
    branch_name = "master"

    add_file_to_repo(temp_repo, file_name, "This note will be deleted.")

    response = client.delete(
        "/apiv1/delete-note",
        json={"repo_path": temp_repo, "note_path": file_name, "branch_name": branch_name}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"

    assert not os.path.exists(os.path.join(temp_repo, file_name))


##### TESTING CONFLICTS #####

def test_create_note_conflict(client, temp_repo):
    """
    For create-note:
      - We first add a file to master (commit A) with initial content.
      - Then we make two additional commits (B and C) on master that update the file.
      - Next, we check out the repository in a detached HEAD state at commit A,
        simulating that the client is working from an outdated commit.
      - Calling create-note now will create a branch from commit A while master is at C.
      - When merging master into the new branch, a conflict is detected.
    """
    file_name = "conflict_note.txt"
    # Commit A: initial file on master.
    add_file_to_repo(temp_repo, file_name, "Initial master content")
    gc = GitCommander(temp_repo)
    old_commit = gc.get_commit_id("master")
    
    # Commits B and C on master: update the file to simulate master advancement.
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master change 1")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master change 1'")
    
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master change 2")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master change 2'")
    
    # Checkout detached at commit A to simulate the client using an outdated commit.
    os.system(f"git -C {temp_repo} checkout --detach {old_commit}")
    
    # Call create-note endpoint; this will create a branch from the outdated commit.
    new_note_content = "New Content from create-note"
    response = client.post(
        "/apiv1/create-note",
        json={
            "repo_path": temp_repo,
            "note_path": file_name,
            "note_value": new_note_content
        }
    )
    data = response.get_json()
    
    # Cleanup: return to master.
    os.system(f"git -C {temp_repo} checkout master")
    
    # Expect that the merge detected a conflict.
    assert response.status_code == 200
    assert data.get("message") == "conflict"
    assert "note" in data
    # The final file content should not simply be the new content.
    assert data["note"] != new_note_content


def test_update_note_conflict(client, temp_repo):
    """
    For update-note:
      - Create the file on master (commit A) and capture its commit id.
      - Then make two commits (B and C) on master that modify the file.
      - Call update-note with the old commit id.
      - The service will create a new branch from commit A and, upon merging master (now at C),
        it will detect a conflict.
    """
    file_name = "existing_conflict_note.txt"
    initial_content = "Initial content."
    updated_content = "Updated conflict content."
    branch_name = "master"
    gc = GitCommander(temp_repo)
    
    # Commit A on master.
    add_file_to_repo(temp_repo, file_name, initial_content)
    old_commit = gc.get_commit_id(branch_name)
    
    # Commits B and C on master.
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master update 1")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master update 1'")
    
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master update 2")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master update 2'")
    
    # Call update-note using the outdated commit id.
    response = client.put(
        "/apiv1/update-note",
        json={
            "repo_path": temp_repo,
            "note_path": file_name,
            "note_value": updated_content,
            "branch_name": branch_name,
            "commit_id": old_commit
        }
    )
    data = response.get_json()
    
    # Expect that the endpoint returns a conflict.
    assert response.status_code == 200
    assert data.get("status") == "conflict"
    # The branch used for resolving conflicts is "user-<file_name>".
    assert data.get("branch_name") == f"user-{file_name}"
    assert "note" in data


def test_delete_note_conflict(client, temp_repo):
    """
    For delete-note:
      - Create the file on master (commit A) and capture its commit id.
      - Then make two commits (B and C) on master that change the file.
      - Check out the repository in detached HEAD at commit A,
        so the deletion branch will be created from the outdated state.
      - Call delete-note; when merging master (advanced to commit C) into the deletion branch,
        a conflict should be detected.
    """
    file_name = "note_conflict_delete.txt"
    branch_name = "master"
    
    # Commit A: create the file.
    add_file_to_repo(temp_repo, file_name, "Initial content for deletion")
    gc = GitCommander(temp_repo)
    old_commit = gc.get_commit_id(branch_name)
    
    # Commits B and C on master.
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master deletion update 1")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master deletion update 1'")
    
    with open(os.path.join(temp_repo, file_name), "w") as f:
        f.write("Master deletion update 2")
    os.system(f"git -C {temp_repo} add {file_name}")
    os.system(f"git -C {temp_repo} commit -m 'Master deletion update 2'")
    
    # Checkout detached at commit A to simulate outdated client state.
    os.system(f"git -C {temp_repo} checkout --detach {old_commit}")
    
    # Call delete-note endpoint.
    response = client.delete(
        "/apiv1/delete-note",
        json={
            "repo_path": temp_repo,
            "note_path": file_name,
            "branch_name": branch_name
        }
    )
    data = response.get_json()
    
    # Cleanup: return to master.
    os.system(f"git -C {temp_repo} checkout master")
    
    # Expect that the deletion endpoint returns a conflict status with a non-null note_value.
    assert response.status_code == 200
    assert data.get("status") == "conflict"
    assert data.get("note_value") is not None


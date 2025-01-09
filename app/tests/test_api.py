import os
import tempfile
import pytest
from app import create_app
from app.utils import create_repo, write_note, list_branches, get_commit_id
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
        create_repo(temp_dir)
        print('in temp-repo', list_branches(temp_dir))
        settings.REPO_PATH = temp_dir
        yield temp_dir



def add_file_to_repo(repo_path, file_name, content=""):
    write_note(repo_path, file_name, content)
    os.system(f"git -C {repo_path} add {file_name}")
    os.system(f"git -C {repo_path} commit -m 'Add {file_name}'")


def test_get_note(client, temp_repo):
    file_name = "test_note.txt"
    branch_name = "master"
    print(list_branches(temp_repo))
    add_file_to_repo(temp_repo, file_name, "This is a test note.")

    response = client.get(f"/apiv1/get-note?note_path={file_name}&branch_name={branch_name}")
    assert response.status_code == 200
    data = response.get_json()
    assert "note" in data
    assert data["note"] == "This is a test note."


def test_get_note_names(client, temp_repo):
    branch_name = "master"
    file_names = [".gitkeep", "note1.txt", "note2.txt", "note3.txt"]
    print(list_branches(temp_repo))
    for file_name in file_names:
        add_file_to_repo(temp_repo, file_name, f"Content of {file_name}")

    response = client.get(f"/apiv1/get-note-names?branch_name={branch_name}")
    data = response.get_json()
    print(data)
    assert response.status_code == 200
    assert "notes" in data
    assert sorted(data["notes"]) == sorted(file_names)


def test_create_note(client, temp_repo):
    file_name = "new_note.txt"
    note_content = "This is a new note."
    print(list_branches(temp_repo))
    response = client.post(
        "/apiv1/create-note",
        json={"note_path": file_name, "note_value": note_content}
    )
    assert response.status_code == 201

    assert os.path.exists(os.path.join(temp_repo, file_name))
    with open(os.path.join(temp_repo, file_name), "r") as f:
        assert f.read() == note_content

def test_update_note(client, temp_repo):
    file_name = "existing_note.txt"
    initial_content = "This is the original content."
    updated_content = "This is the updated content."
    branch_name = "master"

    add_file_to_repo(temp_repo, file_name, initial_content)
    commit_id = get_commit_id(temp_repo, branch_name)

    response = client.put(
        "/apiv1/update-note",
        json={
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
        json={"note_path": file_name, "branch_name": branch_name}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert f"Note '{file_name}' deleted." in data["message"]

    assert not os.path.exists(os.path.join(temp_repo, file_name))


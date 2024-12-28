import os
import tempfile
import pytest
from app.main import app
from app.utils import create_repo, write_note, show_file, file_exists
from config import settings

@pytest.fixture
def client():
    app.config["TESTING"] = True
    
    with app.app_context():
        with app.test_client() as client:
            yield client

@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as temp_dir:
        create_repo(temp_dir)
        settings.REPO_PATH = temp_dir
        yield temp_dir



def add_file_to_repo(repo_path, file_name, content=""):
    write_note(repo_path, file_name, content)
    os.system(f"git -C {repo_path} add {file_name}")
    os.system(f"git -C {repo_path} commit -m 'Add {file_name}'")


def test_get_note(client, temp_repo):
    file_name = "test_note.txt"
    branch_name = "master"
    add_file_to_repo(temp_repo, file_name, "This is a test note.")

    response = client.get(f"/apiv1/get-note?note_path={file_name}&branch_name={branch_name}")
    assert response.status_code == 200
    data = response.get_json()
    assert "note" in data
    assert data["note"] == "This is a test note."


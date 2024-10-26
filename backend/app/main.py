from enum import Enum
from subprocess import run

from blacksheep import Application, get, post, put, delete


class ErrorStatus(Enum):
    ok = 0
    error = 1


REPO_PATH = '/home/mark/projects/playground/wenote-repo'
DEBUG_MODE = True
app = None


def setup():
    global app
    app = Application()


setup()


# create branch, make changes, delete branch

@get('/apiv1.0/get-note')
def get_note(note_path: str, branch_name: str):
    output = run(["git", "show", f"{branch_name}:{note_path}"],
                 capture_output=True,
                 cwd=REPO_PATH)
    if output.stderr:
        if DEBUG_MODE:
            return {'status': ErrorStatus.error, 'error': output.stderr.decode()}
        else:
            return {'status': ErrorStatus.error}

    return {'status': ErrorStatus.ok, 'content': output.stdout.decode()}


@post('/apiv1.0/create-note')
def create_note(note_name: str, note_value: str):
    return {"privet": "omlet"}


@put('/apiv1.0/update-note')
def update_note(note_name: str, note_value: str):
    return {"privet": "omlet"}


@delete('/apiv1.0/delete-note')
def delete_note(note_name: str, note_value: str):
    return {"privet": "omlet"}

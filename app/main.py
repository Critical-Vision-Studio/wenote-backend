import sys
import os

from blacksheep import Application, get, post, put, delete

sys.path.append(os.path.abspath('../'))

from wenote.config import settings
from utils import show_file, commit, checkout_branch, add_file
from exceptions import ErrorStatus

app = Application()


# create branch, make changes, delete branch

@get('/apiv1/get-note')
def get_note(note_path: str, branch_name: str):
    note = show_file(settings.REPO_PATH, note_path, branch_name)

    return {'status': ErrorStatus.ok, 'content': note}


@post('/apiv1/create-note')
def create_note(note_path: str, note_value: str):
    checkout_branch(settings.REPO_PATH, f"user-{note_path}")

    with open(settings.REPO_PATH+note_path, 'w+') as fh:
        fh.write(note_value)

    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, f"user-{note_path}", note_path)

    return {'status': ErrorStatus.ok}


@put('/apiv1/update-note')
def update_note(note_name: str, note_value: str, branch_name: str):
    return {"privet": "omlet"}


@delete('/apiv1/delete-note')
def delete_note(note_name: str, note_value: str):
    return {"privet": "omlet"}



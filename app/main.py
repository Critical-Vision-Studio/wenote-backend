from dataclasses import dataclass
import sys
import os

from blacksheep import FromJSON
from blacksheep import Application, get, post, put, delete
from blacksheep.server.responses import ok, created, file, json

sys.path.append(os.path.abspath('../'))

from config import settings
from app.utils import show_file, commit, checkout_branch, add_file, branch_exists, write_note, merge, create_branch, delete_branch
from app.exceptions import LogicalError
from app.middlewares import exception_handler_middleware


app = Application()
app.middlewares.append(exception_handler_middleware)

app.use_cors(
    allow_methods="*",
    allow_origins="*",
    allow_headers="* Authorization",
    max_age=300,
)


# create branch, make changes, delete branch
@get('/apiv1/get-note')
def get_note(note_path: str, branch_name: str):
    note = show_file(settings.REPO_PATH, note_path, branch_name)

    return json({"note": note})


@post('/apiv1/create-note')
def create_note(note_path: str, note_value: str):
    branch_name = f"user-{note_path}"

    if branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    create_branch(settings.REPO_PATH, branch_name)
    write_note(settings.REPO_PATH, note_path, note_value)
    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, branch_name, note_path, "msg")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if not conflict:
        checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
        conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
        if conflict:
            raise LogicalError(f"Unexpected conflicts while merging {branch_name} into master")
        delete_branch(settings.REPO_PATH, branch_name)
    else:
        commit(settings.REPO_PATH, branch_name, note_path, "msg")

    return created()

@dataclass
class UpdateNoteInput:
    note_path: str
    note_value: str


@put('/apiv1/update-note')
def update_note(input_: FromJSON[UpdateNoteInput]):
    note_path: str = input_.value.note_path
    note_value: str = input_.value.note_value
    branch_name = f"user-{note_path}"

    if branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    create_branch(settings.REPO_PATH, branch_name)
    write_note(settings.REPO_PATH, note_path, note_value)
    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, note_path, f"update {note_path}")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if not conflict:
        checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
        conflict_on_main = merge(settings.REPO_PATH, branch_name)
        if conflict_on_main:
            raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}")
        delete_branch(settings.REPO_PATH, branch_name)
    else:
        #commit(settings.REPO_PATH, branch_name, note_path, "conflict")
        with open(settings.REPO_PATH+note_path, "r") as f:
            return json({"status": "conflict", "note": f.read()})

    print('in the end')
    return json({"status": "ok", "note": show_file(settings.REPO_PATH, note_path, settings.MAIN_BRANCH)})




@delete('/apiv1/delete-note')
def delete_note():
    ...


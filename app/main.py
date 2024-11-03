import sys
import os

from blacksheep import Application, get, post, put, delete
from blacksheep.server.responses import ok, created, file, json

sys.path.append(os.path.abspath('../'))

from config import settings
from app.utils import show_file, commit, checkout_branch, add_file, branch_exists, write_note, merge
from app.exceptions import LogicalError
from middlewares import exception_handler_middleware


app = Application()
app.middlewares.append(exception_handler_middleware)


# create branch, make changes, delete branch
@get('/apiv1/get-note')
def get_note(note_path: str, branch_name: str):
    note = show_file(settings.REPO_PATH, note_path, branch_name)

    return file(note, content_type)


@post('/apiv1/create-note')
def create_note(note_path: str, note_value: str):
    branch_name = f"user-{note_path}"

    if branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    checkout_branch(settings.REPO_PATH, branch_name)
    write_note(settings.REPO_PATH, note_path, note_value)
    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, branch_name, note_path)

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if not conflict:
        checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
        conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
        if conflict:
            raise LogicalError(f"Unexpected conflicts while merging {branch_name} into master")
        delete_branch(settings.REPO_PATH, branch_name)
    else:
        commit(settings.REPO_PATH, branch_name, note_path)
        return Responsee

    return created()


@put('/apiv1/update-note')
def update_note(note_path: str, note_value: str):
    branch_name = f"user-{note_path}"

    if branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    checkout_branch(settings.REPO_PATH, branch_name)
    # todo: file must exist
    write_note(settings.REPO_PATH, note_path, note_value)
    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, branch_name, note_path, f"update {note_path}")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if not conflict:
        checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
        conflict_on_main = merge(settings.REPO_PATH, branch_name)
        if conflict_on_main:
            raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}")
        delete_branch(settings.REPO_PATH, branch_name)
    else:
        commit(settings.REPO_PATH, branch_name, note_path, "conflict ")
        # todo: return Response
        return json({"status": "conflict", "note": show_file(settings.REPO_PATH, note_path, branch_name)})

    return json({"status": "ok", "note": show_file(settings.REPO_PATH, note_path, branch_name)})




@delete('/apiv1/delete-note')
def delete_note():
    ...


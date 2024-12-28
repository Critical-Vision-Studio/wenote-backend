from dataclasses import dataclass
from flask import Flask, request, jsonify
import sys
import os

sys.path.append(os.path.abspath("../"))

from config import settings
from app.utils import *
from app.exceptions import LogicalError
from app.cps import mask_conflicts
from app.middlewares import exception_handler_middleware

app = Flask(__name__)

app.wsgi_app = exception_handler_middleware(app.wsgi_app)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "* Authorization"
    response.headers["Access-Control-Max-Age"] = "300"
    return response


@app.route("/apiv1/get-note", methods=["GET"])
def get_note():
    note_path = request.args.get("note_path")
    branch_name = request.args.get("branch_name")

    if not note_path or not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    file_exists(settings.REPO_PATH, note_path, branch_name)
    note = show_file(settings.REPO_PATH, note_path, branch_name)

    readonly = False

    return jsonify(
        {
            "note": note,
            "readonly": readonly,
            "commit_id": get_commit_id(settings.REPO_PATH, branch_name),
        }
    )


@app.route("/apiv1/get-note-names/", methods=["GET"])
def get_notes():
    branch_name = request.args.get("branch_name")
    if not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    if not branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch does not exist - {branch_name}")

    if branch_name != get_current_branch(settings.REPO_PATH):
        checkout_branch(settings.REPO_PATH, branch_name)

    files = list_files(settings.REPO_PATH, branch_name)
    return jsonify({"branch_name": branch_name, "notes": files})


@app.route("/apiv1/create-note", methods=["POST"])
def create_note():
    data = request.json
    note_path = data.get("note_path")
    note_value = data.get("note_value")

    if not note_path or not note_value:
        return jsonify({"error": "Missing required parameters"}), 400

    branch_name = f"user-{note_path}"

    if branch_exists(settings.REPO_PATH, branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    create_branch(settings.REPO_PATH, branch_name)
    write_note(settings.REPO_PATH, note_path, note_value)
    add_file(settings.REPO_PATH, note_path)
    commit(settings.REPO_PATH, note_path, "msg")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(settings.REPO_PATH, note_path)
        commit(settings.REPO_PATH, note_path, f"conflict with {note_path}")
        merge(settings.REPO_PATH, settings.MAIN_BRANCH)

        note_value = show_file(settings.REPO_PATH, note_path, settings.MAIN_BRANCH)
        return jsonify({"status": "conflict", "note": note_value})

    checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if conflict:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into master")
    delete_branch(settings.REPO_PATH, branch_name)

    return jsonify({"status": "created"}), 201


@dataclass
class UpdateNoteInput:
    note_path: str
    note_value: str
    branch_name: str
    commit_id: str


@dataclass
class DeleteNoteInput:
    note_path: str
    branch_name: str


@app.route("/apiv1/update-note", methods=["PUT"])
def update_note():
    data = request.json
    input_ = UpdateNoteInput(**data)

    if not branch_exists(settings.REPO_PATH, input_.branch_name):
        raise LogicalError(f"branch name does not exist - {input_.branch_name}")

    if input_.commit_id != get_commit_id(settings.REPO_PATH, input_.branch_name):
        raise LogicalError("REQUEST_STATE_OUTDATED")

    branch_name = input_.branch_name
    if branch_name == "master":
        branch_name = f"user-{input_.note_path}"
        if branch_exists(settings.REPO_PATH, branch_name):
            raise LogicalError(f"branch name already exists - {branch_name}")
        create_branch(settings.REPO_PATH, branch_name)

    write_note(settings.REPO_PATH, input_.note_path, input_.note_value)
    add_file(settings.REPO_PATH, input_.note_path)
    commit(settings.REPO_PATH, input_.note_path, f"update {input_.note_path}")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(settings.REPO_PATH, input_.note_path)
        commit(settings.REPO_PATH, input_.note_path, f"conflict with {input_.note_path}")

        return jsonify(
            {
                "status": "conflict",
                "note": show_file(settings.REPO_PATH, input_.note_path, branch_name),
                "branch_name": branch_name,
                "commit_id": get_commit_id(settings.REPO_PATH, "HEAD"),
            }
        )

    checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
    conflict_on_main = merge(settings.REPO_PATH, branch_name)
    if conflict_on_main:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}")
    delete_branch(settings.REPO_PATH, branch_name)

    return jsonify(
        {
            "status": "ok",
            "note": show_file(settings.REPO_PATH, input_.note_path, settings.MAIN_BRANCH),
            "branch_name": settings.MAIN_BRANCH,
            "commit_id": get_commit_id(settings.REPO_PATH, "HEAD"),
        }
    )


@app.route("/apiv1/delete-note", methods=["DELETE"])
def delete_note():
    data = request.json
    input_ = DeleteNoteInput(**data)

    file_exists(settings.REPO_PATH, input_.note_path, input_.branch_name)

    branch_name = f"user-delete-{input_.note_path}"
    create_branch(settings.REPO_PATH, branch_name)

    delete_file(settings.REPO_PATH, input_.note_path)
    commit(settings.REPO_PATH, input_.note_path, f"deleted {input_.note_path}")

    conflict = merge(settings.REPO_PATH, settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(settings.REPO_PATH, input_.note_path)
        commit(settings.REPO_PATH, input_.note_path, f"conflict with deletion of {input_.note_path}")

        note_value = show_file(settings.REPO_PATH, input_.note_path, settings.MAIN_BRANCH)
        return jsonify({"status": "conflict", "note": note_value})

    checkout_branch(settings.REPO_PATH, settings.MAIN_BRANCH)
    conflict_on_main = merge(settings.REPO_PATH, branch_name)
    if conflict_on_main:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}.")

    delete_branch(settings.REPO_PATH, branch_name)

    return jsonify({"status": "ok", "message": f"Note '{input_.note_path}' deleted."})


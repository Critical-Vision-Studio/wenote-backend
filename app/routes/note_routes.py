from flask import request, jsonify
import sys
import os

sys.path.append(os.path.abspath("../"))

from config import settings
from app.utils import GitCommander
from app.exceptions import LogicalError
from app.cps import mask_conflicts
from app.routes import bp as app
from app.serializers import UpdateNoteInput, DeleteNoteInput
from app.services import update_note


@app.route("/apiv1/get-note", methods=["GET"])
def get_note():
    note_path = request.args.get("note_path")
    branch_name = request.args.get("branch_name")

    if not note_path or not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    git = GitCommander(settings.REPO_PATH)
    git.file_exists(note_path, branch_name)
    note = git.show_file(note_path, branch_name)

    readonly = False  # TODO: implement, when we will have users

    return jsonify(
        {
            "note": note,
            "readonly": readonly,
            "commit_id": git.get_commit_id(branch_name),
        }
    )


@app.route("/apiv1/get-note-names", methods=["GET"])
def get_note_names():
    branch_name = request.args.get("branch_name")
    if not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    git = GitCommander(settings.REPO_PATH)
    if not git.branch_exists(branch_name):
        raise LogicalError(f"branch does not exist - {branch_name}")

    if branch_name != git.get_current_branch():
        git.checkout_branch(branch_name)

    files = git.list_files(branch_name)
    git.checkout_branch("master")  # TODO: no hardcode
    return jsonify({"branch_name": branch_name, "notes": files})


@app.route("/apiv1/create-note", methods=["POST"])
def create_note():
    data = request.json
    note_path = data.get("note_path")
    note_value = data.get("note_value")

    git = GitCommander(settings.REPO_PATH)
    if not note_path or not note_value:
        return jsonify({"error": "Missing required parameters"}), 400

    branch_name = f"user-{note_path}"

    if git.branch_exists(branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    git.create_branch(branch_name)
    git.write_note(note_path, note_value)
    git.add_file(note_path)
    git.commit(msg=f"update {note_path}")

    conflict = git.merge(settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(settings.REPO_PATH, note_path)
        git.add_file(note_path)
        git.commit(msg=f"conflict with {note_path}")
        git.merge(settings.MAIN_BRANCH)

        note_value = git.show_file(note_path, settings.MAIN_BRANCH)
        return jsonify({"status": "conflict", "note": note_value})

    git.checkout_branch(settings.MAIN_BRANCH)
    conflict = git.merge(branch_name)
    if conflict:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into master")
    git.delete_branch(branch_name)
    return jsonify({"status": "created"}), 201


@app.route("/apiv1/update-note", methods=["PUT"])
def update_note_view():
    data = request.json
    input_ = UpdateNoteInput(**data)

    status, note_value, branch_name, commit_id = update_note(input_.) # TODO: REPO_PATH also change that model class.
   
    return jsonify(
        {
            "status": status,
            "note": note_value, 
            "branch_name": branch_name,
            "commit_id": commit_id,
        }
    )


@app.route("/apiv1/delete-note", methods=["DELETE"])
def delete_note():
    data = request.json
    input_ = DeleteNoteInput(**data)

    git = GitCommander(settings.REPO_PATH)
    git.file_exists(input_.note_path, input_.branch_name)

    branch_name = f"user-delete-{input_.note_path}"
    git.create_branch(branch_name)

    git.delete_file(input_.note_path)
    git.commit(msg=f"deleted {input_.note_path}")

    conflict = git.merge(settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(settings.REPO_PATH, input_.note_path)
        git.add_file(input_.note_path)
        git.commit(msg=f"conflict with deletion of {input_.note_path}")

        note_value = git.show_file(input_.note_path, settings.MAIN_BRANCH)
        return jsonify({"status": "conflict", "note": note_value})

    git.checkout_branch(settings.MAIN_BRANCH)
    conflict_on_main = git.merge(branch_name)
    if conflict_on_main:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}.")

    git.delete_branch(branch_name)

    return jsonify({"status": "ok", "message": f"Note '{input_.note_path}' deleted."})


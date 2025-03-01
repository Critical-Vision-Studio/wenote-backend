from flask import request, jsonify
import sys
import os

sys.path.append(os.path.abspath("../"))

from app.routes import bp as app
from app.serializers import UpdateNoteInput, DeleteNoteInput
from app.services import update_note, delete_note, create_note, get_note, get_note_names


@app.route("/apiv1/get-note", methods=["GET"])
def get_note_view():
    repo_path = request.args.get("repo_path")
    note_path = request.args.get("note_path")
    branch_name = request.args.get("branch_name")

    if not note_path or not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    data: dict = get_note(repo_path, note_path, branch_name)

    return jsonify(data)


@app.route("/apiv1/get-note-names", methods=["GET"])
def get_note_names_view():
    repo_path = request.args.get("repo_path")
    branch_name = request.args.get("branch_name")

    if not branch_name:
        return jsonify({"error": "Missing required parameters"}), 400

    data: dict = get_note_names(repo_path, branch_name)

    return jsonify(data)


@app.route("/apiv1/create-note", methods=["POST"])
def create_note_view():
    data = request.json
    repo_path = data.get("repo_path")
    note_path = data.get("note_path")
    note_value = data.get("note_value")

    data: dict = create_note(repo_path, note_path, note_value)

    return jsonify(data)


@app.route("/apiv1/update-note", methods=["PUT"])
def update_note_view():
    data = request.json
    input_ = UpdateNoteInput(**data)

    status, note_value, branch_name, commit_id = update_note(input_.repo_path, 
                                                             input_.branch_name,
                                                             input_.commit_id,
                                                             input_.note_path,
                                                             input_.note_value) 
   
    return jsonify(
        {
            "status": status,
            "note": note_value, 
            "branch_name": branch_name,
            "commit_id": commit_id,
        }
    )


@app.route("/apiv1/delete-note", methods=["DELETE"])
def delete_note_view():
    data = request.json
    input_ = DeleteNoteInput(**data)

    status, note_value = delete_note(input_.repo_path, 
                                     input_.note_path, 
                                     input_.branch_name)

    return jsonify({"status": status, "note_value": note_value or None})


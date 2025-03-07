from flask import request, jsonify
import sys
import os
import re
from pathlib import Path
import unicodedata

sys.path.append(os.path.abspath("../"))

from app.routes import bp as app
from app.serializers import UpdateNoteInput, DeleteNoteInput
from app.services import update_note, delete_note, create_note, get_note, get_note_names
from app.exceptions import LogicalError

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PATH_LENGTH = 255
MAX_FILENAME_LENGTH = 255
SYSTEM_FILES = {'.git', '.gitignore', '.DS_Store', 'Thumbs.db', 'desktop.ini'}

def validate_path(path: str) -> bool:
    """Validate file path for security and correctness."""
    if not path:
        return False
    
    # Check for path traversal
    if any(x in path for x in ['..', '//', '\\']):
        return False
    
    # Check for absolute paths
    if os.path.isabs(path):
        return False
    
    # Check path length
    if len(path) > MAX_PATH_LENGTH:
        return False
    
    # Check for control characters
    if any(unicodedata.category(c).startswith('C') for c in path):
        return False
    
    return True

def validate_filename(filename: str) -> bool:
    """Validate filename for security and correctness."""
    if not filename:
        return False
    
    # Check length
    if len(filename) > MAX_FILENAME_LENGTH:
        return False
    
    # Check for system files
    if filename in SYSTEM_FILES:
        return False
    
    # Check for invalid characters
    if re.search(r'[<>:"/\\|?*]', filename):
        return False
    
    # Check for control characters
    if any(unicodedata.category(c).startswith('C') for c in filename):
        return False
    
    return True

def validate_content(content: str) -> bool:
    """Validate note content."""
    if content is None:
        return False
    
    # Check size
    if len(content.encode('utf-8')) > MAX_FILE_SIZE:
        return False
    
    # Check for control characters
    if any(unicodedata.category(c).startswith('C') for c in content):
        return False
    
    return True

def validate_repo_path(repo_path: str) -> bool:
    """Validate repository path."""
    if not repo_path:
        return False
    
    # Check if path exists and is a directory
    if not os.path.isdir(repo_path):
        return False
    
    # Check if it's a git repository
    if not os.path.exists(os.path.join(repo_path, '.git')):
        return False
    
    return True

@app.route("/apiv1/get-note", methods=["GET"])
def get_note_view():
    repo_path = request.args.get("repo_path")
    note_path = request.args.get("note_path")
    branch_name = request.args.get("branch_name")

    # Input validation
    if not all([repo_path, note_path, branch_name]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    if not validate_repo_path(repo_path):
        return jsonify({"error": "Invalid repository path"}), 400
    
    if not validate_path(note_path):
        return jsonify({"error": "Invalid note path"}), 400

    try:
        data: dict = get_note(repo_path, note_path, branch_name)
        return jsonify(data)
    except LogicalError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/apiv1/get-note-names", methods=["GET"])
def get_note_names_view():
    repo_path = request.args.get("repo_path")
    branch_name = request.args.get("branch_name")

    # Input validation
    if not all([repo_path, branch_name]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    if not validate_repo_path(repo_path):
        return jsonify({"error": "Invalid repository path"}), 400

    try:
        data: dict = get_note_names(repo_path, branch_name)
        return jsonify(data)
    except LogicalError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/apiv1/create-note", methods=["POST"])
def create_note_view():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    repo_path = data.get("repo_path")
    note_path = data.get("note_path")
    note_value = data.get("note_value")

    # Input validation
    if not all([repo_path, note_path, note_value is not None]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    if not validate_repo_path(repo_path):
        return jsonify({"error": "Invalid repository path"}), 400
    
    if not validate_path(note_path):
        return jsonify({"error": "Invalid note path"}), 400
    
    if not validate_content(note_value):
        return jsonify({"error": "Invalid note content"}), 400

    try:
        data: dict = create_note(repo_path, note_path, note_value)
        return jsonify(data)
    except LogicalError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/apiv1/update-note", methods=["PUT"])
def update_note_view():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        input_ = UpdateNoteInput(**data)
    except Exception as e:
        return jsonify({"error": "Invalid input data"}), 400

    # Input validation
    if not validate_repo_path(input_.repo_path):
        return jsonify({"error": "Invalid repository path"}), 400
    
    if not validate_path(input_.note_path):
        return jsonify({"error": "Invalid note path"}), 400
    
    if not validate_content(input_.note_value):
        return jsonify({"error": "Invalid note content"}), 400

    try:
        status, note_value, branch_name, commit_id = update_note(
            input_.repo_path,
            input_.branch_name,
            input_.commit_id,
            input_.note_path,
            input_.note_value
        )
        return jsonify({
            "status": status,
            "note": note_value,
            "branch_name": branch_name,
            "commit_id": commit_id,
        })
    except LogicalError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/apiv1/delete-note", methods=["DELETE"])
def delete_note_view():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        input_ = DeleteNoteInput(**data)
    except Exception as e:
        return jsonify({"error": "Invalid input data"}), 400

    # Input validation
    if not validate_repo_path(input_.repo_path):
        return jsonify({"error": "Invalid repository path"}), 400
    
    if not validate_path(input_.note_path):
        return jsonify({"error": "Invalid note path"}), 400

    try:
        status, note_value = delete_note(
            input_.repo_path,
            input_.note_path,
            input_.branch_name
        )
        return jsonify({"status": status, "note_value": note_value or None})
    except LogicalError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


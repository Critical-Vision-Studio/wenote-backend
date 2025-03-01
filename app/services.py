"""Bussiness logic of note route endpoints.


Typical usage example:
    create_or_checkout_to_conflict_branch(GitCommander, 
"""

from .utils import GitCommander
from .exceptions import LogicalError
from config import settings
from app.cps import mask_conflicts


def get_note(repo_path: str, note_path: str, branch_name: str):
    """Gives note value.
 
    Args:

    Returns:

    Raises:
    """
    git = GitCommander(repo_path)
    git.file_exists(note_path, branch_name)
    note = git.show_file(note_path, branch_name)

    readonly = False  # TODO: implement, when we will have users

    return {
            "note": note,
            "readonly": readonly,
            "commit_id": git.get_commit_id(branch_name),
        }


def get_note_names(repo_path: str, branch_name: str):
    """Gives all files present in given repo.
    
    Args:

    Returns:

    Raises:

    """
    git = GitCommander(repo_path)
    if not git.branch_exists(branch_name):
        raise LogicalError(f"branch does not exist - {branch_name}")

    if branch_name != git.get_current_branch():
        git.checkout_branch(branch_name)

    files = git.list_files(branch_name)
    git.checkout_branch(settings.MAIN_BRANCH)

    return {"branch_name": branch_name, "notes": files}


def create_note(repo_path: str, note_path: str, note_value: str) -> dict:
    """Creates note in given repo.

    Args:
        repo_path: -
        note_path: -
        note_value: -

    Returns:
        dictionary with status code and corresponding message.


    Raises:
        LogicalError: New branch name already exists.
        LogicalError: Unexpected confilcts emerged.

    """
    git = GitCommander(repo_path)
    if not note_path or not note_value:
        return {"status": 400, "message": "Missing required parameters"}

    branch_name = f"user-{note_path}"

    if git.branch_exists(branch_name):
        raise LogicalError(f"branch name already exists - {branch_name}")

    git.create_branch(branch_name)
    git.write_note(note_path, note_value)
    git.add_file(note_path)
    git.commit(msg=f"update {note_path}")

    conflict = git.merge(settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(repo_path, note_path)
        git.add_file(note_path)
        git.commit(msg=f"conflict with {note_path}")
        git.merge(settings.MAIN_BRANCH)

        note_value = git.show_file(note_path, settings.MAIN_BRANCH)
        return {"status": 201, "message": "conflict", "note": note_value}

    git.checkout_branch(settings.MAIN_BRANCH)
    conflict = git.merge(branch_name)
    if conflict:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into master")
    git.delete_branch(branch_name)

    return {"status": 201, "message": "created"}


def update_note(repo_path: str, branch_name: str, commit_id: str,
                note_path: str, note_value:str) -> tuple:
    """Updates note in given repo.
    If not on conflict branch -> creates new branch from given commit id.
    If on conflict branch and on last commit -> checkout to that branch. 

    Args:
        git: GitCommander.
        branch_name: branch_name from the user.
        commit_id: commit_id from the user.
        note_path: path to the note.

    Returns:
        status code, note value, branch name, commit id

    Raises:
        LogicalError: Given branch name does not exist. 
        LogicalError: New branch name already exists.
        LogicalError: User commit id is behind HEAD.
    """

    git = GitCommander(repo_path)
    on_conflict_branch = git.is_conflict_branch(branch_name)
    not_head_commit = commit_id != git.get_commit_id(branch_name)

    if not git.branch_exists(branch_name):
        raise LogicalError(f"branch name does not exist - {branch_name}")

    if not on_conflict_branch:
        branch_name = f"user-{note_path}"
    
        if git.branch_exists(branch_name):
            raise LogicalError(f"branch name already exists - {branch_name}")
        
        git.checkout_branch(commit_id)
        git.create_branch(branch_name)
    elif not_head_commit:  # avoid fixing conflicts based on older commit
        raise LogicalError(
            "REQUEST_STATE_OUTDATED Incoming changes against older commit "
            "- conflict resolution supported only against branch HEAD."
        )
    else:  # on conflict branch and on head (can resolve conflicts)
        git.checkout_branch(branch_name)
    
    git.write_note(note_path, note_value)
    git.add_file(note_path)
    git.commit(msg=f"update {note_path}")

    conflict = git.merge(settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(repo_path, note_path)
        git.add_file(note_path) 
        git.commit(msg=f"conflict with {note_path}")
        git.checkout_branch(settings.MAIN_BRANCH)

        return ("conflict", git.show_file(note_path, branch_name),
                branch_name, git.get_commit_id(branch_name))

    git.checkout_branch(settings.MAIN_BRANCH)
    conflict_on_main = git.merge(branch_name)
    if conflict_on_main:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}")
    
    if branch_name == "master":
        raise LogicalError("Unexpected branch: cannot delete master")

    git.delete_branch(branch_name)
    return ("ok", git.show_file(note_path, settings.MAIN_BRANCH),
            settings.MAIN_BRANCH,git.get_commit_id("HEAD"))


def delete_note(repo_path: str, note_path: str, branch_name: str):
    git = GitCommander(repo_path)
    git.file_exists(note_path, branch_name)

    branch_name = f"user-delete-{note_path}"
    git.create_branch(branch_name)

    git.delete_file(note_path)
    git.commit(msg=f"deleted {note_path}")

    conflict = git.merge(settings.MAIN_BRANCH)
    if conflict:
        mask_conflicts(repo_path, note_path)
        git.add_file(note_path)
        git.commit(msg=f"conflict with deletion of {note_path}")

        note_value = git.show_file(note_path, settings.MAIN_BRANCH)
        return "conflict", note_value

    git.checkout_branch(settings.MAIN_BRANCH)
    conflict_on_main = git.merge(branch_name)
    if conflict_on_main:
        raise LogicalError(f"Unexpected conflicts while merging {branch_name} into {settings.MAIN_BRANCH}.")

    git.delete_branch(branch_name)

    return "ok", None


def write_add_commit(git, note_path, note_value):
    """

    """
    git.write_note(note_path, note_value)
    git.add_file(note_path)
    git.commit(msg=f"update {note_path}")


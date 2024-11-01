from subprocess import run

from git import Repo
from git.exc import NoSuchPathError



def create_repo(path: str) -> Repo | None:
    """Creates repo, if it does not exist."""
    # todo: replace git Repo with subprocess
    try:
        return Repo(path)
    except NoSuchPathError:
        return Repo.init(path)


def show_file(repo_path: str, note_path: str, branch_name: str):
    """Shows file from path and specified branch"""
    output = run(["git", "show", f"{branch_name}:{note_path}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def checkout_branch(repo_path: str, branch_name: str):
    output = run(["git", "checkout -b", f"{branch_name}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def write_(repo_path: str, note_name: str, note_value: str):
    with open(repo_path+note_name, 'w+') as fh:
        fh.write(note_value)


def add_file(repo_path: str, file: str):
    output = run(["git", "add", f"{file}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def commit(repo_path: str, branch_name: str, file: str):
    output = run(["git", "commit", f"{branch_name}:{file}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def _check_output(output):
    print(type(output))
    if output.stderr:
        # todo: log this.
        # todo: raise exception here
        print(output.stderr)
        return False 
    return output.stdout.decode()


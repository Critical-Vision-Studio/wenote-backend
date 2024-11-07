from os import linesep
from subprocess import run, CompletedProcess

from app.exceptions import LogicalError

# todo: create class that will handle user (and branch) switching automatically

def create_repo(repo_path: str) -> None:
    """Creates repo, if it does not exist."""
    output = run(["git", "-C", ".", "rev-parse", "2>/dev/null;", "echo $?"],
        capture_output=True,
        cwd=repo_path)
    
    if output:
        # todo: check for errors:
        run(["git", "init"],
            capture_output=True,
            cwd=repo_path)


def switch_user():
    ...
        

def show_file(repo_path: str, note_path: str, branch_name: str):
    """Shows file from path and specified branch"""
    output = run(["git", "show", f"{branch_name}:{note_path}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def create_branch(repo_path: str, branch_name: str):
    output = run(["git", "checkout", "-b", f"{branch_name}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)

def checkout_branch(repo_path: str, branch_name: str):
    output = run(["git", "checkout", f"{branch_name}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)

def list_branches(repo_path: str, name: str):
    output = run(["git", "branch", "-l", f"{name}"],
                     capture_output=True,
                     cwd=repo_path)

    return _check_output(output)


def branch_exists(repo_path:str, name: str):
    branch_count = list_branches(repo_path, name).count(linesep)
    if not branch_count:
        return False
    if branch_count > 1:
        raise LogicalError(f"{name}, {branch_count}, in branch_exists func")
    return True


def write_note(repo_path: str, note_path: str, note_value: str) -> None:
    with open(repo_path+note_path, 'w+') as fh:
        fh.write(note_value)


def add_file(repo_path: str, file: str):
    output = run(["git", "add", f"{file}"],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def commit(repo_path: str, file_path: str, msg: str):
    output = run(["git", "commit", f"{file_path}", "-m", msg],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output)


def merge(repo_path: str, main_branch: str):
    output = run(["git", "merge", main_branch],
                     capture_output=True,
                     cwd=repo_path)
    return "CONFLICT" in _check_output(output)


def delete_branch(repo_path: str, branch_name: str):
    # todo: check status if delete failed
    output = run(["git", "branch", "-d", branch_name],
                         capture_output=True,
                         cwd=repo_path)
    return _check_output(output)



def _check_output(output: CompletedProcess):
    if output.stderr:
        print(output.stderr)
        #raise LogicalError(output.stderr)
    return output.stdout.decode()


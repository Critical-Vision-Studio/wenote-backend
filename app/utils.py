import os

from subprocess import run, CompletedProcess

from app.exceptions import LogicalError

# todo: create class that will handle user (and branch) switching automatically

def create_repo(repo_path: str) -> None:
    """Creates repo, if it does not exist."""
    output = run(["git", "-C", ".", "rev-parse", "2>/dev/null;", "echo $?"],
        capture_output=True,
        cwd=repo_path)
    if output.stdout.decode() == "0":
        print('repo already exists!!!')
        return

    output = run(["git", "init"],
        capture_output=True,
        cwd=repo_path)
    _check_output(output)


def get_commit_id(repo_path: str, from_: str):
    output = run(["git", "rev-parse", from_],
                 capture_output=True,
                 cwd=repo_path)

    return _check_output(output).strip("\n")



def switch_user():
    ...


def file_exists(repo_path: str, note_path: str, branch_name: str):
    output = run(["git", "cat-file", "-e", f"{branch_name}:{note_path}"],
                 capture_output=True,
                 cwd=repo_path)

    return not _check_output(output)


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
    branch_count = list_branches(repo_path, name).count(os.linesep)
    if not branch_count:
        return False
    if branch_count > 1:
        raise LogicalError(f"{name}, {branch_count}, in branch_exists func")
    return True


def write_note(repo_path: str, note_path: str, note_value: str) -> None:
    with open(os.path.join(repo_path, note_path), 'w+') as fh:
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


def delete_branch(repo_path: str, branch_name: str, force: bool = False):
    # todo: check status if delete failed
    output = run(["git", "branch", "-D" if force else "-d", branch_name],
                         capture_output=True,
                         cwd=repo_path)
    return _check_output(output)


def delete_file(repo_path: str, note_path: str):
    output = run(["git", "rm", note_path],
                         capture_output=True,
                         cwd=repo_path)
    return _check_output(output)



def list_files(repo_path: str, branch_name: str) -> list:
    output = run(["git", "ls-tree", "-r", f"{branch_name}", "--name-only"],
                  capture_output=True,
                  cwd=repo_path)

    return _check_output(output).splitlines() 


def get_current_branch(repo_path: str):
    output = run(["git", "branch", "--show-current"],
                  capture_output=True,
                  cwd=repo_path)

    return _check_output(output).strip("\n")


def _check_output(output: CompletedProcess):
    check_for_error = lambda stream: b"error" in stream or b"fatal" in stream 
    if check_for_error(output.stderr) or check_for_error(output.stderr):
       print("ERR: in check_output:", output.stderr)
       raise LogicalError(output.stderr)

    return output.stdout.decode()


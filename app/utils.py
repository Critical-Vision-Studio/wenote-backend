import os
from subprocess import run, CompletedProcess

from app.exceptions import LogicalError

class GitCommander:
    def __init__(self, repo_path: str):
        """
        Initialize with the repository path.
        """
        self.repo_path = repo_path

    def _check_output(self, output: CompletedProcess) -> str:
        """
        Checks for errors in the CompletedProcess and returns the stdout as a string.
        """
        def check_for_error(stream: bytes) -> bool:
            return b"error" in stream or b"fatal" in stream

        if check_for_error(output.stderr):
            print("ERR: in _check_output:", output.stderr)
            raise LogicalError(output.stderr)
        return output.stdout.decode()

    def create_repo(self) -> None:
        """
        Creates a Git repository with a default branch, if it does not exist.
        """
        output = run(
            ["git", "-C", self.repo_path, "rev-parse", "--is-inside-work-tree"],
            capture_output=True
        )
        if output.returncode == 0 and output.stdout.decode().strip() == "true":
            print("Repository already exists!")
            return

        output = run(["git", "init"], capture_output=True, cwd=self.repo_path)
        self._check_output(output)

        # Create an initial commit to ensure a default branch exists.
        initial_file = os.path.join(self.repo_path, ".gitkeep")
        with open(initial_file, "w") as f:
            f.write("")
        run(["git", "add", ".gitkeep"], capture_output=True, cwd=self.repo_path)
        output = run(
            ["git", "commit", "-m", "Initial commit"],
            capture_output=True,
            cwd=self.repo_path
        )
        self._check_output(output)

    def get_commit_id(self, from_: str) -> str:
        output = run(
            ["git", "rev-parse", from_],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output).strip("\n")

    def switch_user(self):
        """
        Placeholder for user (and branch) switching logic.
        """
        # TODO: Implement user switching logic as needed.
        pass

    def file_exists(self, note_path: str, branch_name: str) -> bool:
        output = run(
            ["git", "cat-file", "-e", f"{branch_name}:{note_path}"],
            capture_output=True,
            cwd=self.repo_path
        )
        return not self._check_output(output)

    def show_file(self, note_path: str, branch_name: str) -> str:
        output = run(
            ["git", "show", f"{branch_name}:{note_path}"],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    # TODO: the function should just create a branch, without checkouting it.
    def create_branch(self, branch_name: str) -> str:
        output = run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def checkout_branch(self, branch_name: str) -> str:
        output = run(
            ["git", "checkout", branch_name],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def list_branches(self, name: str = "--all") -> str:
        output = run(
            ["git", "branch", "-l", name],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def branch_exists(self, name: str) -> bool:
        branch_list = self.list_branches(name)
        branch_count = branch_list.count(os.linesep)
        if branch_count == 0:
            return False
        if branch_count > 1:
            raise LogicalError(f"Ambiguous branch '{name}': {branch_count} matches found.")
        return True

    def write_note(self, note_path: str, note_value: str) -> None:
        full_path = os.path.join(self.repo_path, note_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w+") as fh:
            fh.write(note_value)

    def add_file(self, file: str) -> str:
        output = run(
            ["git", "add", file],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def commit(self, file_path: str, msg: str) -> str:
        output = run(
            ["git", "commit", file_path, "-m", msg],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def merge(self, branch: str) -> bool:
        output = run(
            ["git", "merge", branch],
            capture_output=True,
            cwd=self.repo_path
        )
        return "CONFLICT" in self._check_output(output)

    def delete_branch(self, branch_name: str, force: bool = False) -> str:
        flag = "-D" if force else "-d"
        output = run(
            ["git", "branch", flag, branch_name],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def delete_file(self, note_path: str) -> str:
        output = run(
            ["git", "rm", note_path],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output)

    def list_files(self, branch_name: str) -> list:
        output = run(
            ["git", "ls-tree", "-r", branch_name, "--name-only"],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output).splitlines()

    def get_current_branch(self) -> str:
        output = run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            cwd=self.repo_path
        )
        return self._check_output(output).strip("\n")

    def is_conflict_branch(self, branch_name: str) -> bool:
        return branch_name.startswith("conflict")



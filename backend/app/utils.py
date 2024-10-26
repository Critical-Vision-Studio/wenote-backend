from git import Repo
from git.exc import NoSuchPathError


def create_repo(path: str) -> Repo | None:
    """Creates repo, if it does not exist."""
    try:
        return Repo(path)
    except NoSuchPathError:
        return Repo.init(path)

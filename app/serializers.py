from dataclasses import dataclass


@dataclass
class UpdateNoteInput:
    repo_name: str
    note_path: str
    note_value: str
    branch_name: str
    commit_id: str


@dataclass
class DeleteNoteInput:
    repo_name: str
    note_path: str
    branch_name: str



conflict_marker_sep = "="*7
conflict_marker_begin = "<"*7
conflict_marker_end = ">"*7
wenote_conflict_marker = "WENOTE_CONFLICT_MARKER"


def mask_conflicts(repo_path: str, file_path: str):
    def is_begin(line: str):
        nonlocal search_for
        if line[:7] == conflict_marker_begin and len(line.split(" ")) == 2:
            search_for = is_sep
            return True
        return False

    def is_sep(line: str):
        nonlocal search_for
        if line[:7] == conflict_marker_sep:
            search_for = is_end
            return True
        return False


    def is_end(line: str):
        nonlocal search_for
        if line[:7] == conflict_marker_end and len(line.split(" ")) == 2:
            search_for = is_begin
            return True
        return False

    search_for = is_begin

    with open(repo_path+file_path, "r") as f:
        file_value = f.readlines()

    for index, line in enumerate(file_value):
        if search_for(line):
            file_value[index] = wenote_conflict_marker + " " + line

    with open(repo_path+file_path, "w") as f:
        f.writelines(file_value)


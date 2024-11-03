from enum import Enum

class ErrorStatus(Enum):
    ok = 0
    error = 1


class LogicalError(Exception):
    def __init__(self, msg, *args, **kwargs):            
        self.msg = f"LogicalError: {msg}"
        super().__init__(msg, args, kwargs)

    def __str__(self):
        return self.msg


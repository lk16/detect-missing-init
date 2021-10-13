from pathlib import Path


class SkippedFolderHandlingException(Exception):
    def __init__(self, message: str, path: Path) -> None:
        self.message = message
        self.path = path


class AbsolutePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Found absolute path in skipped folders"
        super().__init__(path=path, **kwargs)


class DuplicatePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Found duplicate path in skipped folders"
        super().__init__(path=path, **kwargs)


class UntrackedPathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Found untracked path in skipped folders"
        super().__init__(path=path, **kwargs)

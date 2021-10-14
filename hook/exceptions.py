from pathlib import Path


class SkippedFolderHandlingException(Exception):
    def __init__(self, message: str, path: Path) -> None:
        self.message = message
        self.path = path


class AbsolutePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped folder has an absolute path"
        super().__init__(path=path, **kwargs)


class DuplicatePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped folders contains a duplicate"
        super().__init__(path=path, **kwargs)


class NotAFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped folders contains item which is not folder"
        super().__init__(path=path, **kwargs)


class UntrackedFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped folder not tracked by git"
        super().__init__(path=path, **kwargs)


class NonExistentFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped path does not exist"
        super().__init__(path=path, **kwargs)


class ForbiddenRelativePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        kwargs = {}
        kwargs["message"] = "Skipped path is forbidden"
        super().__init__(path=path, **kwargs)

from pathlib import Path


class SkippedFolderHandlingException(Exception):
    def __init__(self, message: str, path: Path) -> None:
        self.message = message
        self.path = path

    def __str__(self) -> str:
        return f"{self.message}: {self.path}"


class AbsolutePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        super().__init__(path=path, message="Skipped folder has an absolute path")


class DuplicatePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        super().__init__(path=path, message="Skipped folders contains a duplicate")


class NotAFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:

        super().__init__(
            path=path, message="Skipped folders contains item which is not folder"
        )


class UntrackedFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        super().__init__(path=path, message="Skipped folder not tracked by git")


class NonExistentFolderException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        super().__init__(path=path, message="Skipped folder does not exist")


class ForbiddenRelativePathException(SkippedFolderHandlingException):
    def __init__(self, path: Path) -> None:
        super().__init__(path=path, message="Skipped folder is forbidden")


class EmptyPathException(SkippedFolderHandlingException):
    def __init__(self) -> None:
        super().__init__(path=Path(), message="Skipped folder is an empty string")

    def __str__(self) -> str:
        return "''"

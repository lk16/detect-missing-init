#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set

from git.cmd import Git

from hook.exceptions import (
    AbsolutePathException,
    DuplicatePathException,
    EmptyPathException,
    ForbiddenRelativePathException,
    NonExistentFolderException,
    NotAFolderException,
    SkippedFolderHandlingException,
    UntrackedFolderException,
)


def get_untracked_files() -> List[Path]:
    raw_output = Git().ls_files("--others", "--exclude-standard")
    return [Path(file).resolve() for file in raw_output.strip().split("\n")]


def track_files(files: Set[Path]) -> None:
    Git().add(*list(files))


def get_tracked_files() -> List[Path]:
    raw_output = Git().ls_files()
    return [Path(file) for file in raw_output.strip().split("\n")]


def get_repository_root() -> Path:
    raw_output = Git().rev_parse("--show-toplevel")
    return Path(raw_output)


def get_folders_with_tracked_files() -> Set[Path]:
    folders = set()
    for file in get_tracked_files():
        for ancestor in file.parents:
            folders.add(ancestor)

    return folders


@lru_cache(maxsize=None)
def contains_python_file(folder: Path) -> bool:
    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".py":
            return True
        if file.is_dir() and contains_python_file(file):
            return True

    return False


def find_missing_init_files(folders: Set[Path]) -> Set[Path]:
    missing_init_files: Set[Path] = set()
    for folder in folders:
        init_path = folder / "__init__.py"
        if not init_path.exists() and contains_python_file(folder):
            missing_init_files.add(init_path)

    return missing_init_files


def check_all_init_files_tracked() -> bool:
    untracked_init_files: List[Path] = []

    for file in get_untracked_files():
        if file.name == "__init__.py":
            untracked_init_files.append(file)

    if untracked_init_files:
        for file in sorted(untracked_init_files):
            print(file)
        print(f"Found {len(untracked_init_files)} untracked __init__.py file(s).")
        return False

    return True


def create_missing_init_files(missing_init_files: Set[Path], track: bool) -> None:
    for file in missing_init_files:
        file.touch()

    if missing_init_files:
        if track:
            track_files(missing_init_files)
            print(f"Added {len(missing_init_files)} missing __init__.py file(s).")
        else:
            print(f"Created {len(missing_init_files)} missing __init__.py file(s).")


def print_missing_init_files(missing_init_files: Set[Path]) -> None:
    for file in sorted(missing_init_files):
        print(file.resolve())

    if missing_init_files:
        print(f"Found {len(missing_init_files)} missing __init__.py file(s).")


def handle_skipped_folders(
    skipped_folders_flag: Optional[str], folders: Set[Path]
) -> Set[Path]:
    if skipped_folders_flag is None:
        return folders

    repo_root = get_repository_root()

    skipped_folders: Set[Path] = set()
    for split_flag in skipped_folders_flag.split(","):

        if split_flag == "":
            raise EmptyPathException()

        path = Path(split_flag)

        if path.is_absolute():
            raise AbsolutePathException(path)

        try:
            Path(repo_root).joinpath(path).resolve().relative_to(repo_root.resolve())
        except ValueError:
            # prevent directory traverssal attack
            raise ForbiddenRelativePathException(path)

        if not path.exists():
            raise NonExistentFolderException(path)

        if not path.is_dir():
            raise NotAFolderException(path)

        if path not in folders:
            raise UntrackedFolderException(path)

        if path in skipped_folders:
            raise DuplicatePathException(path)

        skipped_folders.add(path)

    for skipped_folder in skipped_folders:
        folders.discard(skipped_folder)

    return folders


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--track", action="store_true")
    parser.add_argument("--expect-root-init", action="store_true")
    parser.add_argument("--skip-folders", dest="skipped_folders")
    parsed_args = parser.parse_args(argv)

    if parsed_args.track and not parsed_args.create:
        print("--track requires --create")
        return 3

    folders = get_folders_with_tracked_files()

    if not parsed_args.expect_root_init:
        folders.discard(Path("."))

    try:
        folders = handle_skipped_folders(parsed_args.skipped_folders, folders)
    except SkippedFolderHandlingException as e:
        print(str(e), file=sys.stderr)
        return 4

    missing_init_files = find_missing_init_files(folders)

    if parsed_args.create:
        create_missing_init_files(missing_init_files, parsed_args.track)
    else:
        print_missing_init_files(missing_init_files)

    if missing_init_files:
        return 1

    if not check_all_init_files_tracked():
        return 2

    return 0


if __name__ == "__main__":
    exit(main())

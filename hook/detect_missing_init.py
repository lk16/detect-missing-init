#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path
from typing import List, Set

from git.cmd import Git


def get_untracked_files() -> List[Path]:
    raw_output = Git().ls_files("--others", "--exclude-standard")
    return [Path(file).resolve() for file in raw_output.strip().split("\n")]


def track_files(files: Set[Path]) -> None:
    Git().add(*list(files))


def get_tracked_files() -> List[Path]:
    raw_output = Git().ls_files()
    return [Path(file) for file in raw_output.strip().split("\n")]


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


def create_missing_init_files(missing_init_files: Set[Path]) -> None:
    for file in missing_init_files:
        file.write_text("\n")

    if missing_init_files:
        print(f"Created {len(missing_init_files)} missing __init__.py file(s).")


def print_missing_init_files(missing_init_files: Set[Path]) -> None:
    for file in sorted(missing_init_files):
        print(file.resolve())

    if missing_init_files:
        print(f"Found {len(missing_init_files)} missing __init__.py file(s).")


def main(argv: List[str]) -> int:
    parser = ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--track", action="store_true")
    parsed_args = parser.parse_args(argv)

    if parsed_args.track and not parsed_args.create:
        print("--track requires --create")
        return 3

    folders = get_folders_with_tracked_files()
    folders.discard(Path("."))

    missing_init_files = find_missing_init_files(folders)

    if parsed_args.create:
        create_missing_init_files(missing_init_files)
    else:
        print_missing_init_files(missing_init_files)

    if parsed_args.track:
        track_files(missing_init_files)

    if missing_init_files:
        return 1

    if not check_all_init_files_tracked():
        return 2

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))

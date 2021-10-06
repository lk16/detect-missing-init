#!/usr/bin/env python
from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path
from typing import List, Set

from git.cmd import Git


def get_untracked_files() -> List[Path]:
    raw_output = Git().ls_files("--others", "--exclude-standard")
    return [Path(file).resolve() for file in raw_output.strip().split("\n")]


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


def find_missing_init_files(folders: Set[Path]) -> List[Path]:
    missing_init_files: List[Path] = []

    for folder in folders:
        init_path = folder / "__init__.py"
        if not init_path.exists() and contains_python_file(folder):
            missing_init_files.append(init_path)

    return missing_init_files


def check_all_init_files_tracked():
    untracked_init_files = list(
        filter(lambda file: file.name == "__init__.py", get_untracked_files())
    )

    if untracked_init_files:
        for file in sorted(untracked_init_files):
            print(file)
        print(f"Found {len(untracked_init_files)} untracked __init__.py file(s).")
        return False
    return True


def add_missing_init_files(missing_init_files: List[Path]) -> None:
    for file in missing_init_files:
        file.write_text("\n")

    if missing_init_files:
        print(f"Created {len(missing_init_files)} missing __init__.py file(s).")


def list_missing_init_files(missing_init_files: List[Path]) -> None:
    for file in sorted(missing_init_files):
        print(file.resolve())

    if missing_init_files:
        print(f"Found {len(missing_init_files)} missing __init__.py file(s).")


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parsed_args = parser.parse_args()

    folders = get_folders_with_tracked_files()

    folders.remove(Path("."))

    missing_init_files = find_missing_init_files(folders)

    if parsed_args.fix:
        add_missing_init_files(missing_init_files)
    else:
        list_missing_init_files(missing_init_files)

    if missing_init_files:
        return 1

    if not check_all_init_files_tracked():
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python
import shlex
import subprocess
import sys
from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set


def run_command(command: str) -> List[str]:
    process = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        check=True,
    )

    raw_output = process.stdout.decode("utf-8")

    if not raw_output:
        return []

    return [line for line in raw_output.strip().split("\n")]


def get_untracked_files() -> List[Path]:
    output_lines = run_command("git ls-files --others --exclude-standard")
    return [Path(line).resolve() for line in output_lines]


def track_files(files: Set[Path]) -> None:
    command = "git add " + " ".join(shlex.quote(str(file)) for file in files)
    run_command(command)


def get_tracked_files() -> List[Path]:
    output_lines = run_command("git ls-files")
    return [Path(line) for line in output_lines]


def get_folders_with_tracked_files() -> Set[Path]:
    folders = set()
    for file in get_tracked_files():
        for ancestor in file.parents:
            folders.add(ancestor)

    return folders


@lru_cache(maxsize=None)
def contains_python_file(folder: Path) -> bool:
    if not folder.exists():
        return False

    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".py":
            return True
        if file.is_dir() and contains_python_file(file):
            return True

    return False


def find_missing_init_files(folders: Set[Path], python_folders: Set[Path]) -> Set[Path]:
    missing_init_files: Set[Path] = set()

    for folder in folders:
        init_path = folder / "__init__.py"

        if all(
            [
                not init_path.exists(),
                contains_python_file(folder),
                set(init_path.parents) & python_folders,
            ]
        ):
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


def main(argv: Optional[List[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--track", action="store_true")
    parser.add_argument("--python-folders", dest="python_folders", required=True)

    parsed_args = parser.parse_args(argv)

    flag_create: bool = parsed_args.create
    flag_python_folders: str = parsed_args.python_folders

    # --create implies --track
    flag_track: bool = parsed_args.track or parsed_args.create

    python_folders: Set[Path] = {
        Path(folder) for folder in flag_python_folders.split(",")
    }

    folders_with_tracked_files = get_folders_with_tracked_files()

    missing_init_files = find_missing_init_files(
        folders_with_tracked_files, python_folders
    )

    if flag_create:
        for file in missing_init_files:
            file.touch()

    if flag_track:
        track_files(missing_init_files)

    for file in sorted(missing_init_files):
        print(file.resolve())

    print(f"Found {len(missing_init_files)} missing __init__.py file(s).")

    if missing_init_files:
        return 1

    if not check_all_init_files_tracked():
        return 2

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))

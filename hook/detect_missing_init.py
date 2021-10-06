import subprocess
from functools import lru_cache
from pathlib import Path
from typing import List


def run_command(command: str) -> List[str]:
    process = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )

    return process.stdout.decode("utf-8").strip().split("\n")


@lru_cache(maxsize=None)
def contains_python_file(folder: Path) -> bool:
    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".py":
            return True
        if file.is_dir() and contains_python_file(file):
            return True

    return False


def main() -> int:
    # TODO parse args
    create_missing = False

    # get absolute path of all non-root folders with git-tracked files
    folders_raw = run_command(
        r"git ls-files | xargs -n 1 dirname | sort | uniq | grep -v '^\.$' | xargs realpath"
    )
    folders = [Path(folder) for folder in folders_raw]

    missing_init_files: List[Path] = []

    for folder in folders:
        init_path = folder / "__init__.py"
        if not init_path.exists() and contains_python_file(folder):
            missing_init_files.append(init_path)

    if create_missing:
        for file in missing_init_files:
            file.touch(mode=0o644)
            file.write_text("\n")
        print(f"Created {len(missing_init_files)} missing __init__.py files.")

    else:
        for file in sorted(missing_init_files):
            print(file.resolve())
        print(f"Found {len(missing_init_files)} missing __init__.py files.")

    if missing_init_files:
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

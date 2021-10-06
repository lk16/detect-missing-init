from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Set
from unittest.mock import Mock

import pytest

from hook import detect_missing_init
from hook.detect_missing_init import (
    check_all_init_files_tracked,
    contains_python_file,
    find_missing_init_files,
    get_folders_with_tracked_files,
)


@pytest.fixture()
def temporary_dir():
    with TemporaryDirectory() as dir:
        yield Path(dir)


@pytest.mark.parametrize(
    ["tracked_files", "folders"],
    [
        ([Path("foo.py")], {Path(".")}),
        ([Path("foo.py"), Path("bar.py")], {Path(".")}),
        ([Path("a/foo.py")], {Path("."), Path("a")}),
        ([Path("a/b/foo.py")], {Path("."), Path("a"), Path("a/b")}),
    ],
)
def test_get_folders_with_tracked_files(tracked_files: List[Path], folders: Set[Path]):
    detect_missing_init.get_tracked_files = Mock(return_value=tracked_files)
    assert get_folders_with_tracked_files() == folders


@pytest.mark.parametrize(
    ["files", "expected_value"],
    [
        ([], False),
        (["a.py"], True),
        (["a.foo", False]),
        (["a.py", "b.py"], True),
        (["a/b.py"], True),
        (["a/b.foo"], False),
    ],
)
def test_contains_python_file(
    temporary_dir: Path, files: List[str], expected_value: bool
):
    for file in files:
        Path(temporary_dir / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_dir / file).touch()

    assert expected_value == contains_python_file(temporary_dir)


@pytest.mark.parametrize(
    ["untracked_files", "expected_value"],
    (
        [[], True],
        [[Path("foo.py")], True],
        [[Path("__init__.py")], False],
        [[Path("a/__init__.py")], False],
        [[Path("venv/somelib/somepackage/__init__.py")], False],
    ),
)
def test_check_all_init_files_tracked(
    untracked_files: List[Path], expected_value: bool
):
    detect_missing_init.get_untracked_files = Mock(return_value=untracked_files)
    assert expected_value == check_all_init_files_tracked()


@pytest.mark.parametrize(
    ["folders", "files", "expected_value"],
    [
        ([], [], {}),
        ([Path(".")], [Path("foo.py")], {Path("__init__.py")}),
        (
            [Path("."), Path("foo")],
            [Path("foo/bar.py")],
            {Path("__init__.py"), Path("foo/__init__.py")},
        ),
    ],
)
def test_find_missing_init_files(
    temporary_dir: Path,
    folders: List[Path],
    files: List[Path],
    expected_value: Set[Path],
):
    for folder in folders:
        Path(temporary_dir / folder).mkdir(parents=True, exist_ok=True)

    for file in files:
        Path(temporary_dir / file).touch()

    resolved_folders = {Path(temporary_dir / folder) for folder in folders}
    resolved_expected_value = {
        Path(temporary_dir / folder) for folder in expected_value
    }
    assert resolved_expected_value == find_missing_init_files(resolved_folders)

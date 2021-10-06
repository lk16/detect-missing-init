from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Set
from unittest.mock import Mock

import pytest

from hook import detect_missing_init
from hook.detect_missing_init import (
    contains_python_file,
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

import contextlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Set, Type, Union
from unittest.mock import Mock

import pytest
from _pytest.capture import CaptureFixture

from hook import detect_missing_init
from hook.detect_missing_init import (
    check_all_init_files_tracked,
    contains_python_file,
    create_missing_init_files,
    find_missing_init_files,
    get_folders_with_tracked_files,
    handle_skipped_folders,
    main,
    print_missing_init_files,
)
from hook.exceptions import (
    AbsolutePathException,
    DuplicatePathException,
    ForbiddenRelativePathException,
    NonExistentFolderException,
    NotAFolderException,
    UntrackedFolderException,
)


@pytest.fixture()
def temporary_directory():
    with TemporaryDirectory() as dir:
        yield Path(dir)


@pytest.fixture(autouse=True)
def clear_contains_pyton_file_cache():
    contains_python_file.cache_clear()


@contextlib.contextmanager
def change_directory(dir: Path):
    old_dir = Path.cwd()
    os.chdir(dir)
    yield
    os.chdir(old_dir)


def get_file_descendants(dir: Path) -> Set[Path]:
    descendants = dir.glob("**/*")
    return set(
        descendant.relative_to(dir)
        for descendant in descendants
        if descendant.is_file()
    )


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
    temporary_directory: Path, files: List[str], expected_value: bool
):
    for file in files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    assert expected_value == contains_python_file(temporary_directory)


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
    temporary_directory: Path,
    folders: List[Path],
    files: List[Path],
    expected_value: Set[Path],
):
    for folder in folders:
        Path(temporary_directory / folder).mkdir(parents=True, exist_ok=True)

    for file in files:
        Path(temporary_directory / file).touch()

    resolved_folders = {Path(temporary_directory / folder) for folder in folders}
    resolved_expected_value = {
        Path(temporary_directory / folder) for folder in expected_value
    }
    assert resolved_expected_value == find_missing_init_files(resolved_folders)


def test_create_missing_init_files(temporary_directory: Path, capsys: CaptureFixture):
    files = {Path("__init__.py"), Path("foo/__init__.py")}
    Path(temporary_directory / "foo").mkdir(parents=True, exist_ok=True)

    with change_directory(temporary_directory):
        create_missing_init_files(files, False)

    for file in files:
        assert Path(temporary_directory / file).exists()

    captured = capsys.readouterr()
    assert captured.out == "Created 2 missing __init__.py file(s).\n"


def test_print_missing_init_files(temporary_directory: Path, capsys: CaptureFixture):
    files = {Path("__init__.py"), Path("foo/__init__.py")}
    Path(temporary_directory / "foo").mkdir(parents=True, exist_ok=True)

    with change_directory(temporary_directory):
        print_missing_init_files(files)

    for file in files:
        assert not Path(temporary_directory / file).exists()

    expected_stdout = ""
    for file in sorted(files):
        expected_stdout += str(Path(temporary_directory / file).resolve()) + "\n"

    expected_stdout += "Found 2 missing __init__.py file(s).\n"

    captured = capsys.readouterr()
    assert expected_stdout == captured.out


@pytest.mark.parametrize(
    [
        "skipped_folders_flag",
        "folders",
        "existing_files",
        "existing_folders",
        "expected_result",
    ],
    [
        (None, {Path(".")}, [], [], {Path(".")}),
        ("foo", {Path("."), Path("foo")}, [], [Path("foo")], {Path(".")}),
        ("/", {Path(".")}, [], [], AbsolutePathException),
        ("/foo/bar", {Path(".")}, [], [], AbsolutePathException),
        ("foo.py", {Path(".")}, [Path("foo.py")], [], NotAFolderException),
        (
            "foo,foo",
            {Path("."), Path("foo")},
            [],
            [Path("foo")],
            DuplicatePathException,
        ),
        ("foo", {Path(".")}, [], [Path("foo")], UntrackedFolderException),
        ("foo", {Path(".")}, [], [], NonExistentFolderException),
        ("..", {Path(".")}, [], [], ForbiddenRelativePathException),
    ],
)
def test_handle_skipped_folders(
    temporary_directory: Path,
    skipped_folders_flag: Optional[str],
    folders: Set[Path],
    existing_files: List[Path],
    existing_folders: List[Path],
    expected_result: Union[Set[Path], Type[Exception]],
):
    detect_missing_init.get_repository_root = Mock(return_value=temporary_directory)

    for file in existing_files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    for folder in existing_folders:
        Path(temporary_directory / folder).mkdir(parents=True, exist_ok=True)

    with change_directory(temporary_directory):
        if isinstance(expected_result, type):
            with pytest.raises(expected_result):
                handle_skipped_folders(skipped_folders_flag, folders)
        else:
            assert expected_result == handle_skipped_folders(
                skipped_folders_flag, folders
            )


@pytest.mark.parametrize(
    ["tracked_files", "untracked_files", "expected_exit_code"],
    [
        ([], [], 0),
        ([Path("foo.py")], [], 0),
        ([Path("foo.bar")], [], 0),
        ([Path("a/foo.py")], [], 1),
        ([Path("a/b/foo.py")], [], 1),
        ([Path("a/b/foo.bar")], [], 0),
        ([], [Path("__init__.py")], 2),
        ([], [Path("a/__init__.py")], 2),
        ([], [Path("a/b/__init__.py")], 2),
        ([], [Path("foo.bar")], 0),
        ([], [Path("a/b/foo.bar")], 0),
    ],
)
def test_main_default(
    temporary_directory: Path,
    tracked_files: List[Path],
    untracked_files: List[Path],
    expected_exit_code: int,
):
    detect_missing_init.get_tracked_files = Mock(return_value=tracked_files)
    detect_missing_init.get_untracked_files = Mock(return_value=untracked_files)

    for file in tracked_files + untracked_files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    with change_directory(temporary_directory):
        assert expected_exit_code == main([])

    expected_file_descendants = set(tracked_files + untracked_files)
    assert expected_file_descendants == get_file_descendants(temporary_directory)


@pytest.mark.parametrize(
    ["tracked_files", "untracked_files", "expected_exit_code"],
    [
        ([], [], 0),
        ([Path("foo.py")], [], 0),
        ([Path("foo.bar")], [], 0),
        ([Path("a/foo.py")], [Path("a/__init__.py")], 2),
        ([Path("a/b/foo.py")], [Path("a/__init__.py"), Path("a/b/__init__.py")], 2),
        ([Path("a/b/foo.bar")], [], 0),
        ([], [Path("__init__.py")], 2),
        ([], [Path("a/__init__.py")], 2),
        ([], [Path("a/b/__init__.py")], 2),
        ([], [Path("foo.bar")], 0),
        ([], [Path("a/b/foo.bar")], 0),
    ],
)
def test_main_create(
    temporary_directory: Path,
    tracked_files: List[Path],
    untracked_files: List[Path],
    expected_exit_code: int,
):
    detect_missing_init.get_tracked_files = Mock(return_value=tracked_files)
    detect_missing_init.get_untracked_files = Mock(return_value=untracked_files)

    for file in tracked_files + untracked_files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    with change_directory(temporary_directory):
        assert expected_exit_code == main(["--create"])

    expected_file_descendants = set(tracked_files + untracked_files)
    assert expected_file_descendants == get_file_descendants(temporary_directory)


def test_main_track_without_create():
    assert 3 == main(["--track"])


@pytest.mark.parametrize(
    ["tracked_files", "untracked_files", "expected_exit_code", "newly_tracked_files"],
    [
        ([], [], 0, set()),
        ([Path("foo.py")], [], 0, set()),
        ([Path("foo.bar")], [], 0, set()),
        ([Path("a/foo.py")], [], 1, {Path("a/__init__.py")}),
        ([Path("a/b/foo.py")], [], 1, {Path("a/__init__.py"), Path("a/b/__init__.py")}),
        ([Path("a/b/foo.bar")], [], 0, set()),
        ([], [Path("__init__.py")], 2, set()),
        ([], [Path("a/__init__.py")], 2, set()),
        ([], [Path("a/b/__init__.py")], 2, set()),
        ([], [Path("foo.bar")], 0, set()),
        ([], [Path("a/b/foo.bar")], 0, set()),
    ],
)
def test_main_track(
    temporary_directory: Path,
    tracked_files: List[Path],
    untracked_files: List[Path],
    expected_exit_code: int,
    newly_tracked_files: Set[Path],
):
    detect_missing_init.get_tracked_files = Mock(return_value=tracked_files)
    detect_missing_init.get_untracked_files = Mock(return_value=untracked_files)
    detect_missing_init.track_files = Mock()

    for file in tracked_files + untracked_files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    with change_directory(temporary_directory):
        assert expected_exit_code == main(["--create", "--track"])

    if newly_tracked_files:
        detect_missing_init.track_files.assert_called_with(newly_tracked_files)
    else:
        detect_missing_init.track_files.assert_not_called()

    expected_file_descendants = set(tracked_files + untracked_files) | set(
        newly_tracked_files
    )
    assert expected_file_descendants == get_file_descendants(temporary_directory)


@pytest.mark.parametrize(
    ["tracked_files", "expected_exit_code"],
    [
        ([], 0),
        ([Path("foo.py")], 1),
        ([Path("foo.bar")], 0),
        ([Path("a/foo.py")], 1),
        ([Path("a/foo.py"), Path("a/__init__.py")], 1),
        ([Path("a/foo.py"), Path("__init__.py"), Path("a/__init__.py")], 0),
        ([Path("a/b/foo.py")], 1),
        (
            [
                Path("a/b/foo.py"),
                Path("__init__.py"),
                Path("a/__init__.py"),
                Path("a/b/__init__.py"),
            ],
            0,
        ),
        ([Path("a/b/foo.bar")], 0),
    ],
)
def test_main_expect_root_init(
    temporary_directory: Path,
    tracked_files: List[Path],
    expected_exit_code: int,
):
    detect_missing_init.get_tracked_files = Mock(return_value=tracked_files)
    detect_missing_init.get_untracked_files = Mock(return_value=[])

    for file in tracked_files:
        Path(temporary_directory / file).parent.mkdir(parents=True, exist_ok=True)
        Path(temporary_directory / file).touch()

    with change_directory(temporary_directory):
        assert expected_exit_code == main(["--expect-root-init"])

    expected_file_descendants = set(tracked_files)
    assert expected_file_descendants == get_file_descendants(temporary_directory)


def test_main_skipped_folders_fail(temporary_directory: Path):
    detect_missing_init.get_repository_root = Mock(return_value=temporary_directory)

    with change_directory(temporary_directory):
        assert 4 == main(["--skip-folders", "foo"])

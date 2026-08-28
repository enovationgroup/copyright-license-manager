from argparse import Namespace

import pytest

from clmgr.handler import (
    ApplyHandler,
    ChangeHandler,
    CheckHandler,
    CountingHandler,
    DiffHandler,
    DryRunHandler,
    count_of_files,
    create_handler,
)


def arguments(dry_run=False, check=False, diff=False):
    return Namespace(dry_run=dry_run, check=check, diff=diff)


class RecordingHandler(CountingHandler):
    """Records the source files it is asked to process"""

    def __init__(self):
        super().__init__()
        self.processed = []

    def process(self, action, path, lines, new_lines):
        self.processed.append(path)


def test_create_apply_handler():
    assert isinstance(create_handler(arguments()), ApplyHandler)


def test_create_dry_run_handler():
    assert isinstance(create_handler(arguments(dry_run=True)), DryRunHandler)


def test_check_decorates_dry_run_handler():
    handler = create_handler(arguments(check=True))

    assert isinstance(handler, CheckHandler)
    assert isinstance(handler.handler, DryRunHandler)


def test_diff_decorates_apply_handler():
    handler = create_handler(arguments(diff=True))

    assert isinstance(handler, DiffHandler)
    assert isinstance(handler.handler, ApplyHandler)


def test_diff_decorates_dry_run_handler():
    handler = create_handler(arguments(dry_run=True, diff=True))

    assert isinstance(handler, DiffHandler)
    assert isinstance(handler.handler, DryRunHandler)


def test_check_and_diff_decorate_dry_run_handler():
    handler = create_handler(arguments(check=True, diff=True))

    assert isinstance(handler, CheckHandler)
    assert isinstance(handler.handler, DiffHandler)
    assert isinstance(handler.handler.handler, DryRunHandler)


def test_handler_is_abstract():
    with pytest.raises(TypeError):
        ChangeHandler()


def test_counting_handler_is_abstract():
    with pytest.raises(TypeError):
        CountingHandler()


def test_handler_counts_every_action():
    handler = RecordingHandler()
    handler.handle("add", "a.py", [], [])
    handler.handle("update", "b.py", [], [])
    handler.handle("none", "c.py", [], [])

    assert handler.added == 1
    assert handler.updated == 1
    assert handler.up_to_date == 1


def test_up_to_date_file_is_processed():
    """A dry run reports every file, so the hook runs for up to date files too"""
    handler = RecordingHandler()
    handler.handle("none", "a.py", [], [])

    assert handler.processed == ["a.py"]


def test_decorator_delegates_to_the_handler_it_extends():
    handler = RecordingHandler()
    decorated = DiffHandler(handler)
    decorated.handle("add", "a.py", [], [])

    assert handler.processed == ["a.py"]
    assert decorated.exit_code() == handler.exit_code()


def test_check_fails_on_change():
    handler = CheckHandler(DryRunHandler())
    handler.handle("update", "a.py", [], [])

    assert handler.exit_code() == 1


def test_check_succeeds_without_change():
    handler = CheckHandler(DryRunHandler())
    handler.handle("none", "a.py", [], [])

    assert handler.exit_code() == 0


def test_dry_run_never_fails():
    handler = DryRunHandler()
    handler.handle("add", "a.py", [], [])

    assert handler.exit_code() == 0


def test_apply_handler_never_fails():
    assert ApplyHandler().exit_code() == 0


def test_count_of_files_is_singular_for_one():
    assert count_of_files(1) == "1 file"


def test_count_of_files_is_plural_for_none():
    assert count_of_files(0) == "0 files"


def test_count_of_files_is_plural_for_many():
    assert count_of_files(2) == "2 files"


def test_summary_uses_the_matching_form(capsys):
    handler = DryRunHandler()
    handler.handle("add", "a.py", [], [])
    handler.handle("none", "b.py", [], [])
    handler.handle("none", "c.py", [], [])
    handler.summarize()

    captured = capsys.readouterr()
    assert "1 file: Copyright would be added" in captured.err
    assert "0 files: Copyright would be updated" in captured.err
    assert "2 files: Copyright up to date" in captured.err

from clmgr.tests.test_base import run_dry_run, run_test, test_dir


def test_diff_applies_changes(capsys):
    """--diff is verbose about the changes, it does not suppress them"""
    test_args = [
        "-c",
        test_dir + "/config/default/single.yml",
        "--file",
        test_dir + "/temp/default/py/single.py",
        "--diff",
    ]

    run_test("default/py/", "single.py", test_args)

    captured = capsys.readouterr()
    assert "+# SPDX-FileCopyrightText: Copyright (c)" in captured.out
    assert "1 file: Copyright added" in captured.err


def test_diff_is_quiet_when_up_to_date(capsys):
    test_args = [
        "-c",
        test_dir + "/config/default/no-change.yml",
        "--file",
        test_dir + "/temp/default/py/no_change.py",
        "--diff",
    ]

    run_test("default/py/", "no_change.py", test_args)

    captured = capsys.readouterr()
    assert "@@" not in captured.out
    assert "1 file: Copyright up to date" in captured.err


def test_diff_stdout_is_a_clean_patch(capsys):
    """Only the diff reaches stdout, so it can be piped into git apply"""
    test_args = [
        "-c",
        test_dir + "/config/default/single.yml",
        "--file",
        test_dir + "/temp/default/py/single.py",
        "--dry-run",
        "--diff",
    ]

    run_dry_run(test_args)

    captured = capsys.readouterr()
    assert captured.out.startswith("---")
    for line in captured.out.splitlines():
        assert line[:1] in ["-", "+", "@", " ", ""]

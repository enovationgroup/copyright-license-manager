from clmgr.tests.test_base import run_dry_run_config, run_dry_run_tree


def test_dry_run_add_java():
    run_dry_run_config("default/java/", "Single.java", "default/single.yml", 0)


def test_dry_run_add_typescript():
    run_dry_run_config("default/ts/", "single.component.ts", "default/single.yml", 0)


def test_dry_run_add_python():
    run_dry_run_config("default/py/", "single.py", "default/single.yml", 0)


def test_dry_run_add_dotnet():
    run_dry_run_config("default/cs/", "Single.cs", "default/single.yml", 0)


def test_dry_run_add_sql():
    run_dry_run_config("default/sql/", "single.sql", "default/single.yml", 0)


def test_dry_run_update():
    run_dry_run_config(
        "default/java/", "SingleUpdate.java", "default/single.update.yml", 0
    )


def test_dry_run_no_change():
    run_dry_run_config("default/py/", "no_change.py", "default/no-change.yml", 0)


def test_check_fails_on_add():
    run_dry_run_config(
        "default/java/", "Single.java", "default/single.yml", 1, ["--check"]
    )


def test_check_fails_on_update():
    run_dry_run_config(
        "default/java/",
        "SingleUpdate.java",
        "default/single.update.yml",
        1,
        ["--check"],
    )


def test_check_passes_on_no_change():
    run_dry_run_config(
        "default/py/", "no_change.py", "default/no-change.yml", 0, ["--check"]
    )


def test_dry_run_with_diff():
    run_dry_run_config(
        "default/py/", "single.py", "default/single.yml", 0, ["--dry-run", "--diff"]
    )


def test_dry_run_reports_action(capsys):
    run_dry_run_config("default/py/", "single.py", "default/single.yml", 0)

    captured = capsys.readouterr()
    assert "would add" in captured.err
    assert "single.py" in captured.err
    assert "1 file: Copyright would be added" in captured.err


def test_dry_run_diff_reports_copyright_line(capsys):
    run_dry_run_config(
        "default/py/", "single.py", "default/single.yml", 0, ["--dry-run", "--diff"]
    )

    captured = capsys.readouterr()
    assert "+# SPDX-FileCopyrightText: Copyright (c)" in captured.out


def test_check_reports_no_change(capsys):
    run_dry_run_config(
        "default/py/", "no_change.py", "default/no-change.yml", 0, ["--check"]
    )

    captured = capsys.readouterr()
    assert "would add" not in captured.err
    assert "would update" not in captured.err
    assert "1 file: Copyright up to date" in captured.err


def test_dry_run_directory():
    run_dry_run_tree("default/", "default/single.yml", 0)


def test_check_directory():
    run_dry_run_tree("default/", "default/single.yml", 1, ["--check"])


def test_dry_run_directory_honours_exclude(capsys):
    run_dry_run_tree("default/", "default/exclude.yml", 0)

    captured = capsys.readouterr()
    assert "Single.java" not in captured.err
    assert "Multiple.java" not in captured.err
    assert "ChangeFormat.java" in captured.err


def test_dry_run_reports_up_to_date_files(capsys):
    run_dry_run_config("default/py/", "no_change.py", "default/no-change.yml", 0)

    captured = capsys.readouterr()
    assert "up to date   " in captured.err
    assert "no_change.py" in captured.err


def test_dry_run_report_columns_line_up(capsys):
    run_dry_run_tree("default/", "default/single.yml", 0)

    captured = capsys.readouterr()
    paths = [line.index(" /") for line in captured.err.splitlines() if " /" in line]

    assert len(paths) > 1
    assert len(set(paths)) == 1


def test_dry_run_writes_nothing_to_stdout(capsys):
    run_dry_run_tree("default/", "default/single.yml", 0)

    captured = capsys.readouterr()
    assert captured.out == ""

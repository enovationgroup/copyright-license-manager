from clmgr.tests.test_base import run_test_config


def test_no_change_java():
    run_test_config("default/java/", "NoChange.java", "default/no-change.yml")


def test_no_change_typescript():
    run_test_config("default/ts/", "no-change.component.ts", "default/no-change.yml")


def test_no_change_python():
    run_test_config("default/py/", "no_change.py", "default/no-change.yml")


def test_no_change_dotnet():
    run_test_config("default/cs/", "NoChange.cs", "default/no-change.yml")


def test_format_no_change_java():
    run_test_config("format/java/", "NoChange.java", "format/no-change.yml")


def test_format_no_change_typescript():
    run_test_config("format/ts/", "no-change.component.ts", "format/no-change.yml")


def test_format_no_change_python():
    run_test_config("format/py/", "no_change.py", "format/no-change.yml")


def test_format_no_change_dotnet():
    run_test_config("format/cs/", "NoChange.cs", "format/no-change.yml")

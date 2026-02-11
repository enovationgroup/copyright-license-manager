from clmgr.tests.test_base import run_test_config


def test_change_format_java():
    run_test_config("default/java/", "ChangeFormat.java", "default/change-format.yml")


def test_change_format_typescript():
    run_test_config(
        "default/ts/", "change-format.component.ts", "default/change-format.yml"
    )


def test_change_format_python():
    run_test_config("default/py/", "change_format.py", "default/change-format.yml")


def test_change_format_dotnet():
    run_test_config("default/cs/", "ChangeFormat.cs", "default/change-format.yml")


def test_format_change_format_java():
    run_test_config("format/java/", "ChangeFormat.java", "format/change-format.yml")


def test_format_change_format_typescript():
    run_test_config(
        "format/ts/", "change-format.component.ts", "format/change-format.yml"
    )


def test_format_change_format_python():
    run_test_config("format/py/", "change_format.py", "format/change-format.yml")


def test_format_change_format_dotnet():
    run_test_config("format/cs/", "ChangeFormat.cs", "format/change-format.yml")

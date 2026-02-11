from clmgr.tests.test_base import run_test_config


def test_remove_java():
    run_test_config("default/java/", "Remove.java", "default/remove.yml")


def test_remove_typescript():
    run_test_config("default/ts/", "remove.component.ts", "default/remove.yml")


def test_remove_python():
    run_test_config("default/py/", "remove.py", "default/remove.yml")


def test_remove_dotnet():
    run_test_config("default/cs/", "Remove.cs", "default/remove.yml")


def test_format_remove_java():
    run_test_config("format/java/", "Remove.java", "format/remove.yml")


def test_format_remove_typescript():
    run_test_config("format/ts/", "remove.component.ts", "format/remove.yml")


def test_format_remove_python():
    run_test_config("format/py/", "remove.py", "format/remove.yml")


def test_format_remove_dotnet():
    run_test_config("format/cs/", "Remove.cs", "format/remove.yml")

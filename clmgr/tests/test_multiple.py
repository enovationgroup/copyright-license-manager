from clmgr.tests.test_base import run_test_config


def test_multiple_java():
    run_test_config("default/java/", "Multiple.java", "default/multiple.yml")


def test_multiple_typescript():
    run_test_config("default/ts/", "multiple.component.ts", "default/multiple.yml")


def test_multiple_python():
    run_test_config("default/py/", "multiple.py", "default/multiple.yml")


def test_multiple_dotnet():
    run_test_config("default/cs/", "Multiple.cs", "default/multiple.yml")


def test_format_multiple_java():
    run_test_config("format/java/", "Multiple.java", "format/multiple.yml")


def test_format_multiple_typescript():
    run_test_config("format/ts/", "multiple.component.ts", "format/multiple.yml")


def test_format_multiple_python():
    run_test_config("format/py/", "multiple.py", "format/multiple.yml")


def test_format_multiple_dotnet():
    run_test_config("format/cs/", "Multiple.cs", "format/multiple.yml")

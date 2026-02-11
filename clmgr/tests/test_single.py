from clmgr.tests.test_base import run_test_config


def test_single_java():
    run_test_config("default/java/", "Single.java", "default/single.yml")


def test_single_typescript():
    run_test_config("default/ts/", "single.component.ts", "default/single.yml")


def test_single_python():
    run_test_config("default/py/", "single.py", "default/single.yml")


def test_single_dotnet():
    run_test_config("default/cs/", "Single.cs", "default/single.yml")


def test_format_single_java():
    run_test_config("format/java/", "Single.java", "format/single.yml")


def test_format_single_typescript():
    run_test_config("format/ts/", "single.component.ts", "format/single.yml")


def test_format_single_python():
    run_test_config("format/py/", "single.py", "format/single.yml")


def test_format_single_dotnet():
    run_test_config("format/cs/", "Single.cs", "format/single.yml")

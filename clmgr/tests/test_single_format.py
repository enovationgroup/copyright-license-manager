from clmgr.tests.test_base import run_test_config


def test_single_format_java():
    run_test_config("java/", "SingleFormat.java", "single.format.yml")


def test_single_format_typescript():
    run_test_config("ts/", "single-format.component.ts", "single.format.yml")


def test_single_format_python():
    run_test_config("py/", "single_format.py", "single.format.yml")


def test_single_format_dotnet():
    run_test_config("cs/", "SingleFormat.cs", "single.format.yml")

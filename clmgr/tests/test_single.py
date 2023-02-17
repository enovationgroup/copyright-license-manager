from clmgr.tests.test_base import run_test_config


def test_single_java():
    run_test_config("java/", "Single.java", "single.yml")


def test_single_typescript():
    run_test_config("ts/", "single.component.ts", "single.yml")


def test_single_python():
    run_test_config("py/", "single.py", "single.yml")


def test_single_dotnet():
    run_test_config("cs/", "Single.cs", "single.yml")

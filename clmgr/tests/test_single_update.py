from clmgr.tests.test_base import run_test_config


def test_single_update_java():
    run_test_config("java/", "SingleUpdate.java", "single.update.yml")


def test_single_update_typescript():
    run_test_config("ts/", "single-update.component.ts", "single.update.yml")


def test_single_update_python():
    run_test_config("py/", "single_update.py", "single.update.yml")


def test_single_update_dotnet():
    run_test_config("cs/", "SingleUpdate.cs", "single.update.yml")

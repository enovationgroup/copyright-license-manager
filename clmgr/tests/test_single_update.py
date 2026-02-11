from clmgr.tests.test_base import run_test_config


def test_single_update_java():
    run_test_config("default/java/", "SingleUpdate.java", "default/single.update.yml")


def test_single_update_typescript():
    run_test_config(
        "default/ts/", "single-update.component.ts", "default/single.update.yml"
    )


def test_single_update_python():
    run_test_config("default/py/", "single_update.py", "default/single.update.yml")


def test_single_update_dotnet():
    run_test_config("default/cs/", "SingleUpdate.cs", "default/single.update.yml")


def test_format_single_update_java():
    run_test_config("format/java/", "SingleUpdate.java", "format/single.update.yml")


def test_format_single_update_typescript():
    run_test_config(
        "format/ts/", "single-update.component.ts", "format/single.update.yml"
    )


def test_format_single_update_python():
    run_test_config("format/py/", "single_update.py", "format/single.update.yml")


def test_format_single_update_dotnet():
    run_test_config("format/cs/", "SingleUpdate.cs", "format/single.update.yml")

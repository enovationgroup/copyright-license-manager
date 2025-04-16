from clmgr.tests.test_base import run_test_config


def test_multiple_update_java():
    run_test_config(
        "default/java/", "MultipleUpdate.java", "default/multiple.update.yml"
    )


def test_multiple_update_typsecript():
    run_test_config(
        "default/ts/", "multiple-update.component.ts", "default/multiple.update.yml"
    )


def test_multiple_update_python():
    run_test_config("default/py/", "multiple_update.py", "default/multiple.update.yml")


def test_multiple_dotnet():
    run_test_config("default/cs/", "MultipleUpdate.cs", "default/multiple.update.yml")


def test_format_multiple_update_java():
    run_test_config("format/java/", "MultipleUpdate.java", "format/multiple.update.yml")


def test_format_multiple_update_typsecript():
    run_test_config(
        "format/ts/", "multiple-update.component.ts", "format/multiple.update.yml"
    )


def test_format_multiple_update_python():
    run_test_config("format/py/", "multiple_update.py", "format/multiple.update.yml")


def test_format_multiple_dotnet():
    run_test_config("format/cs/", "MultipleUpdate.cs", "format/multiple.update.yml")

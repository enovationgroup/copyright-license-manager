from clmgr.tests.test_base import run_test_config


def test_no_change_java():
    run_test_config("default/java/", "NoChange.java", "default/single.yml")


def test_no_change_typescript():
    run_test_config("default/ts/", "no-change.component.ts", "default/single.yml")


def test_no_change_python():
    run_test_config("default/py/", "no_change.py", "default/single.yml")


def test_no_change_dotnet():
    run_test_config("default/cs/", "NoChange.cs", "default/single.yml")


# def test_format_no_change_java():
#     run_test_config("format/java/", "Single.java", "format/single.yml")
#
#
# def test_format_no_change_typescript():
#     run_test_config("format/ts/", "single.component.ts", "format/single.yml")
#
#
# def test_format_no_change_python():
#     run_test_config("format/py/", "single.py", "format/single.yml")
#
#
# def test_format_no_change_dotnet():
#     run_test_config("format/cs/", "Single.cs", "format/single.yml")

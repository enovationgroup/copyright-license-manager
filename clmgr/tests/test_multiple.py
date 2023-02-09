from clmgr.tests.test_base import run_test_config


def test_multiple_java():
    run_test_config("java/", "Multiple.java", "multiple.yml")


def test_multiple_typescript():
    run_test_config("ts/", "multiple.component.ts", "multiple.yml")

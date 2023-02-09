from clmgr.tests.test_base import run_test_config


def test_remove_java():
    run_test_config("java/", "Remove.java", "remove.yml")


def test_remove_typescript():
    run_test_config("ts/", "remove.component.ts", "remove.yml")

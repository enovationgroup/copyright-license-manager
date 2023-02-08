from clmgr.tests.test_base import run_test_config


def test_multiple_update_java():
    run_test_config("java/", "MultipleUpdate.java", "multiple.update.yml")


def test_multiple_update_typsecript():
    run_test_config("ts/", "multiple-update.component.ts", "multiple.update.yml")

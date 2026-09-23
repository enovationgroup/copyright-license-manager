from clmgr.main import main
from clmgr.tests.test_base import test_dir


def run_dry_run(extra_args):
    return main(
        [
            "-c",
            test_dir + "/config/default/single.yml",
            "--file",
            test_dir + "/input/default/py/single.py",
            "--dry-run",
        ]
        + extra_args
    )


def test_processed_files_are_not_reported_by_default(caplog):
    run_dry_run([])

    assert "Processing file" not in caplog.text


def test_processed_files_are_reported_with_debug(caplog):
    run_dry_run(["--debug"])

    assert "Processing file" in caplog.text

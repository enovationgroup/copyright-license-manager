"""A second run of clmgr must not change a file it has already processed"""

import glob
import os
import re

import pytest

from clmgr.main import main
from clmgr.template import sources
from clmgr.tests.test_base import test_dir

# Scenarios whose name differs from their configuration file
CONFIGS = {
    "single-update": "single.update",
    "multiple-update": "multiple.update",
    "comments-update": "comments",
    "prologue": "single",
    "prologue-xml": "single",
    "prologue-update": "single.update",
    "first-line": "single.update",
}

OUTPUTS = sorted(glob.glob(test_dir + "/output/*/*/*.*"))


def scenario(path):
    """Derive the scenario from names such as SingleUpdate.cs or single_update.py"""
    name = os.path.basename(path).split(".")[0]
    name = re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()
    return name.replace("_", "-")


def test_every_source_has_output():
    extensions = {os.path.basename(path).rsplit(".", 1)[1] for path in OUTPUTS}

    assert extensions == set(sources)


@pytest.mark.parametrize(
    "path", OUTPUTS, ids=[os.path.relpath(p, test_dir) for p in OUTPUTS]
)
def test_second_run_changes_nothing(path):
    directory = os.path.relpath(path, test_dir + "/output").split(os.sep)[0]
    name = scenario(path)
    config = f"{test_dir}/config/{directory}/{CONFIGS.get(name, name)}.yml"
    assert os.path.exists(
        config
    ), f"no configuration for scenario '{name}', add it to CONFIGS"

    assert main(["-c", config, "--file", path, "--check"]) == 0

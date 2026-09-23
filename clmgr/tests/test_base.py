import filecmp
import glob
import os
import shutil

from pathlib import Path

from clmgr.main import main

test_dir = os.path.dirname(os.path.realpath(__file__))


def run_test_config(directory, filename, config):
    test_args = [
        "-c",
        test_dir + "/config/" + config,
        "--file",
        test_dir + "/temp/" + directory + filename,
    ]

    run_test(directory, filename, test_args)


def run_test(directory, filename, test_args):
    input_file = test_dir + "/input/" + directory + filename
    temp_file = test_dir + "/temp/" + directory + filename
    output_file = test_dir + "/output/" + directory + filename

    # Create a temp dir to run the tests on
    os.makedirs(test_dir + "/temp/" + directory, exist_ok=True)
    shutil.copy(input_file, temp_file)
    shutil.copystat(input_file, temp_file)

    # Run clmgr
    main(test_args)

    # Verify result
    assert filecmp.cmp(
        temp_file,
        output_file,
        shallow=False,
    )


def run_dry_run_config(directory, filename, config, expected_exit, extra_args=None):
    """Run clmgr on a single file without applying any change.

    Verifies the reported exit code and that the source file is left exactly as
    it was, without any leftover temporary file.
    """
    input_file = test_dir + "/input/" + directory + filename
    temp_dir = test_dir + "/temp/" + directory
    temp_file = temp_dir + filename

    # Create a temp dir to run the tests on
    os.makedirs(temp_dir, exist_ok=True)
    shutil.copy(input_file, temp_file)
    shutil.copystat(input_file, temp_file)

    test_args = [
        "-c",
        test_dir + "/config/" + config,
        "--file",
        temp_file,
    ] + (extra_args or ["--dry-run"])

    # Run clmgr
    exit_code = main(test_args)

    # Verify result
    assert exit_code == expected_exit
    assert filecmp.cmp(temp_file, input_file, shallow=False)
    assert glob.glob(temp_dir + "/*.tmp") == []
    assert glob.glob(temp_dir + "/*.bak") == []


def run_dry_run(test_args):
    """Run clmgr on a copy of a single input file and return the exit code"""
    filename = Path(test_args[test_args.index("--file") + 1]).name
    input_file = test_dir + "/input/default/py/" + filename
    temp_dir = test_dir + "/temp/default/py/"

    os.makedirs(temp_dir, exist_ok=True)
    shutil.copy(input_file, temp_dir + filename)

    return main(test_args)


def run_dry_run_tree(directory, config, expected_exit, extra_args=None):
    """Run clmgr on a directory without applying any change.

    Verifies the reported exit code and that every file in the tree is left
    exactly as it was.
    """
    input_tree = test_dir + "/input/" + directory
    temp_tree = test_dir + "/temp/dry-run/" + directory

    # Create a temp tree to run the tests on
    if os.path.exists(temp_tree):
        shutil.rmtree(temp_tree)
    shutil.copytree(input_tree, temp_tree)

    test_args = [
        "-c",
        test_dir + "/config/" + config,
        "-d",
        temp_tree,
    ] + (extra_args or ["--dry-run"])

    # Run clmgr
    exit_code = main(test_args)

    # Verify result
    assert exit_code == expected_exit
    assert_tree_unchanged(input_tree, temp_tree)


def assert_tree_unchanged(input_tree, temp_tree):
    for root, _, files in os.walk(input_tree):
        for name in files:
            source = os.path.join(root, name)
            target = os.path.join(temp_tree, os.path.relpath(source, input_tree))

            assert os.path.exists(target)
            assert filecmp.cmp(source, target, shallow=False)

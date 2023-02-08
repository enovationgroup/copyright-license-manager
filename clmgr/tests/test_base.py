import filecmp
import os
import shutil

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
    global test_dir

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

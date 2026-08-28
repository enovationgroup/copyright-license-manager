import sys

from pathlib import Path
from pprint import pformat

from clmgr.args import (
    apply_config_defaults,
    handle_config_file,
    handle_debug,
    handle_input_dir,
    handle_version,
    parse_args,
    read_config,
    validate_config,
)
from clmgr.log import setup_custom_logger
from clmgr.paths import select_files
from clmgr.processor import process_lines

log = setup_custom_logger("root")


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    args = parse_args(args)

    handle_version(args)
    handle_debug(args, log)
    config_file = handle_config_file(args)
    input_dir = handle_input_dir(args)

    # Load Configuration
    cfg = read_config(config_file)
    validate_config(cfg, config_file)
    cfg = apply_config_defaults(cfg)
    log.debug(f"Configuration: \n{pformat(cfg, indent=2)}")

    # Process Input
    # Input can be one of the following:
    #  * file
    #  * directory
    # however please note that the configuration must always be provided either present from
    # the current working directory or through the flag -c, --config
    add = 0
    upd = 0
    utd = 0

    for ext in cfg["source"]:
        if args.file is not None:
            file_list = []
            path = Path(args.file)
            if path.suffix.lower()[1:] == ext:
                file_list.append(path)
        else:
            file_list = select_files(input_dir, ext, cfg["include"], cfg["exclude"])

        for file in file_list:
            log.info(f"Processing file: {file}")

            # Read source and close it
            src = open(file=file.absolute(), encoding="utf-8", mode="r")
            lines = src.readlines()
            src.close()

            # Process file
            res = process_lines(cfg, file, ext, lines, args)
            add += res[0]
            upd += res[1]
            utd += res[2]

    print(f"[{add}] Copyright added")
    print(f"[{upd}] Copyright updated")
    print(f"[{utd}] Copyright up to date")

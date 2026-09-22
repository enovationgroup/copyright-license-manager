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
from clmgr.handler import create_handler
from clmgr.log import setup_custom_logger
from clmgr.template import licenses
from clmgr.paths import select_files
from clmgr.processor import (
  analyze,
  process_lines
)

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

    # A dry run reports the changes, any other run applies them
    handler = create_handler(args)

    # Process Input
    # Input can be one of the following:
    #  * file
    #  * directory
    # however please note that the configuration must always be provided either present from
    # the current working directory or through the flag -c, --config

    for ext in cfg["source"]:
        if args.file is not None:
            file_list = []
            path = Path(args.file)
            if path.suffix.lower()[1:] == ext:
                file_list.append(path)
        else:
            file_list = select_files(input_dir, ext, cfg["include"], cfg["exclude"])

        for file in file_list:
            log.debug(f"Processing file: {file}")

            # Read source and close it
            src = open(file=file.absolute(), encoding="utf-8", mode="r")
            lines = src.readlines()
            src.close()

            # Determine what would happen to this file and let the
            # handler either apply or report it
            action, new_lines = analyze(cfg, ext, lines, args)
            handler.handle(action, file, lines, new_lines)

    handler.summarize()

    return handler.exit_code()

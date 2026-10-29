import os
import sys

from pathlib import Path, PurePath
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
from clmgr.paths import SourceError, select_sources, source_extension
from clmgr.processor import analyze

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

    try:
        if args.file is not None:
            file_list = select_file(input_dir, Path(args.file), cfg["source"])
        else:
            file_list = select_sources(
                input_dir, cfg["source"], cfg["include"], cfg["exclude"]
            )
    except SourceError as error:
        for message in str(error).splitlines():
            log.error(message)
        sys.exit(2)

    for file, ext in file_list:
        log.debug(f"Processing file: {file}")

        # Read source and close it
        try:
            with open(file=file.absolute(), encoding="utf-8", mode="r") as src:
                lines = src.readlines()
        except UnicodeDecodeError:
            log.warning(f"Skipping {file}, it is not UTF-8 encoded")
            continue

        # Determine what would happen to this file and let the
        # handler either apply or report it
        action, new_lines = analyze(cfg, ext, lines, file, args)
        handler.handle(action, file, lines, new_lines)

    handler.summarize()

    return handler.exit_code()


def select_file(input_dir, path, source):
    """Select a single file given with -i/--file, by the source option

    The include patterns of a type are matched against the path relative to
    the input directory, as when the directory is walked.

    Returns
    -------
        A list with the tuple (path, ext), or an empty list when the file is
        not a source

    """
    try:
        relative_path = PurePath(os.path.relpath(path.absolute(), input_dir))
    except ValueError:
        # On Windows a file on another drive has no relative path
        relative_path = PurePath(path.name)

    ext = source_extension(source, relative_path.as_posix(), path)

    return [] if ext is None else [(path, ext)]

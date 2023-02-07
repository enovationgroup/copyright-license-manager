from fnmatch import fnmatch, translate
import os
import re
import sys

from pathlib import Path
from pprint import pformat

from clmgr.args import (
    handle_config_file,
    handle_debug,
    handle_input_dir,
    handle_version,
    parse_args,
    read_config,
)
from clmgr.log import setup_custom_logger
from clmgr.processor import process_lines
from clmgr.template import licenses


log = setup_custom_logger("root")


class ContinueIgnore(Exception):
    pass


def main(args=sys.argv[1:]):
    args = parse_args(args)

    handle_version(args)
    handle_debug(args, log)
    config_file = handle_config_file(args)
    input_dir = handle_input_dir(args)

    # Load Configuration
    cfg = read_config(config_file)
    if "include" not in cfg.keys() or cfg["include"] is None:
        cfg["include"] = []
    if "exclude" not in cfg.keys() or cfg["exclude"] is None:
        cfg["exclude"] = []
    if "license" not in cfg.keys() or cfg["license"] is None:
        cfg["license"]["enabled"] = False
    if cfg["license"]["enabled"]:
        if (
            "external" not in cfg["license"].keys()
            or cfg["license"]["external"] is None
        ):
            cfg["license"]["external"] = False
        if "content" not in cfg["license"].keys() or cfg["license"]["content"] is None:
            cfg["license"]["content"] = licenses.get("default")
    log.debug(f"Configuration:\n{pformat(cfg, indent=2)}")

    # Process Input
    # Input can be one of the following:
    #  * file
    #  * directory
    # however please note that the configuration must always be provided either present from
    # the current working directory or through the flag -c, --config
    add = 0
    upd = 0

    includes = r"|".join([translate(i) for i in cfg["include"]])
    excludes = r"|".join([translate(e) for e in cfg["exclude"]]) or r"$."

    for ext in cfg["source"]:
        file_list = []
        if args.file is not None:
            path = Path(args.file)
            if path.suffix.lower()[1:] == ext:
                file_list.append(path)
        else:
            for root, dirs, files in os.walk(input_dir, topdown=True):
                # exclude dirs based on directory name only
                dirs[:] = [d for d in dirs if not re.match(excludes, d)]
                # convert dirs to full path
                dirs[:] = [os.path.join(root, d) for d in dirs]
                # exclude directories on full path
                dirs[:] = [d for d in dirs if not re.match(excludes, d)]

                # exclude/include files
                files[:] = [f for f in files if fnmatch(f, "*." + ext)]
                files[:] = [os.path.join(root, f) for f in files]
                files[:] = [f for f in files if Path(f).stem not in excludes]
                files[:] = [f for f in files if Path(f).name not in excludes]
                files[:] = [f for f in files if not re.match(excludes, f)]
                files[:] = [f for f in files if re.match(includes, f)]
                for file in files:
                    file_list.append(Path(root, file))

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

    print(f"[{add}] Copyright added")
    print(f"[{upd}] Copyright Updated")

"""Utilities for parsing and handling commandline arguments"""

import argparse
import logging
from string import Formatter
from pathlib import Path
import sys
import yaml

from clmgr.__version__ import get_versions
from clmgr.template import licenses, placeholders, sources

log = logging.getLogger("root")

# Configuration options without a usable default
REQUIRED_OPTIONS = ["source", "legal"]

# Properties every entry of the legal option must define
REQUIRED_LEGAL_PROPERTIES = ["inception", "name", "locality", "country"]


def parse_args(args):
    # Create argument parser
    def formatter_class(prog):
        return argparse.HelpFormatter(  # noqa: E731
            prog, max_help_position=100, width=200
        )

    parser = argparse.ArgumentParser(prog="clmgr", formatter_class=formatter_class)

    # Configure commandline options
    parser.add_argument(
        "-c", "--config", help="configuration file", default="copyright.yml"
    )
    # TODO: add stdin support
    # TODO: add input file support
    parser.add_argument("-i", "--file", help="input file", metavar="FILE")
    parser.add_argument(
        "-d", "--dir", help="input directory", default=Path.cwd(), metavar="DIR"
    )
    parser.add_argument(
        "--region",
        help="Copyright search region; default=10",
        type=int,
        default=10,
        metavar="REGION",
    )
    parser.add_argument("--debug", help="Verbose logging", action="store_true")
    parser.add_argument("--version", help="Show version", action="store_true")

    # Parse Arguments
    return parser.parse_args(args)


def handle_version(args):
    """Print the version number if --version argument is provided on commandline

    Parameters
    ----------
    args
        Parsed commandline arguments

    Returns
    -------
        None

    """
    if args.version:
        print(get_versions()["version"])
        sys.exit()


def handle_debug(args, logger):
    """Handle --debug commandline option

    Parameters
    ----------
    args
        Parsed commandline arguments
    """
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logger.setLevel(log_level)


def handle_config_file(args):
    config_file = Path(args.config).absolute()
    if not Path.exists(config_file):
        log.error(f"Unable to find configuration {config_file}")
        sys.exit(2)
    return config_file


# Validate Input Directory
# The input directory defaults to current working directory
# So when using this with stdin this validation will
# not cause any errors
def handle_input_dir(args):
    input_dir = Path(args.dir).absolute()
    if not Path.exists(input_dir):
        log.error(f"Input directory {input_dir} does not exists")
        sys.exit(2)
    return input_dir


def read_config(config_file):
    log.debug(f"Reading configuration from: {config_file}")
    try:
        with open(file=config_file, encoding="utf-8", mode="r") as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as error:
        log.error(f"Unable to parse configuration {config_file}: {error}")
        sys.exit(2)
    except OSError as error:
        log.error(f"Unable to read configuration {config_file}: {error}")
        sys.exit(2)


def validate_config(cfg, config_file):
    """Verify that the configuration can be used to process source files

    Reports every problem that is found before exiting, so a broken
    configuration does not have to be fixed one message at a time.

    Parameters
    ----------
    cfg
        Parsed configuration
    config_file
        Path of the configuration file, used for reporting

    Returns
    -------
        None

    """
    if cfg is None:
        log.error(
            f"Configuration {config_file} is empty, "
            f"it must define `{'` and `'.join(REQUIRED_OPTIONS)}`"
        )
        sys.exit(2)

    if not isinstance(cfg, dict):
        log.error(
            f"Configuration {config_file} must be a mapping of configuration options"
        )
        sys.exit(2)

    errors = []
    for option in REQUIRED_OPTIONS:
        value = cfg.get(option)
        if value is None:
            errors.append(f"missing required option '{option}'")
        elif not isinstance(value, list) or len(value) == 0:
            errors.append(f"option '{option}' must be a non empty list")

    if not errors:
        errors.extend(validate_source(cfg["source"]))
        errors.extend(validate_legal(cfg["legal"]))
        errors.extend(validate_format(cfg.get("format")))

    if errors:
        for error in errors:
            log.error(f"Configuration {config_file}: {error}")
        sys.exit(2)


def validate_source(source):
    """Verify that every configured source file extension is supported"""
    supported = ", ".join(sorted(sources))

    return [
        f"source '{ext}' is not supported, supported are: {supported}"
        for ext in source
        if ext not in sources
    ]


def validate_format(copyright_format):
    """Verify that a copyright format only uses placeholders clmgr fills in"""
    if copyright_format is None:
        return []

    used = [
        name.split(".")[0].split("[")[0]
        for _, name, _, _ in Formatter().parse(copyright_format)
        if name
    ]

    return [
        f"format uses unknown placeholder '{name}', "
        f"available are: {', '.join(placeholders)}"
        for name in used
        if name not in placeholders
    ]


def validate_legal(legal):
    """Verify that every legal entity defines the properties of the format"""
    errors = []
    for idx, entity in enumerate(legal):
        if not isinstance(entity, dict):
            errors.append(f"legal entity [{idx}] must be a mapping of properties")
            continue

        missing = [key for key in REQUIRED_LEGAL_PROPERTIES if entity.get(key) is None]
        if missing:
            errors.append(f"legal entity [{idx}] is missing: {', '.join(missing)}")

    return errors


def apply_config_defaults(cfg):
    """Fill in the configuration options that have a default

    Parameters
    ----------
    cfg
        Validated configuration

    Returns
    -------
        The configuration, with every optional option filled in

    """
    if cfg.get("include") is None:
        cfg["include"] = []
    if cfg.get("exclude") is None:
        cfg["exclude"] = []
    if cfg.get("license") is None:
        cfg["license"] = {}
    if cfg["license"].get("enabled") is None:
        cfg["license"]["enabled"] = False
    if cfg["license"]["enabled"]:
        if cfg["license"].get("external") is None:
            cfg["license"]["external"] = False
        if cfg["license"].get("content") is None:
            cfg["license"]["content"] = licenses.get("default")
    if cfg.get("format") is None:
        cfg["format"] = (
            "SPDX-FileCopyrightText: Copyright (c) {inception} - {year} "
            "[{name} - {locality} - {country}]"
        )

    return cfg

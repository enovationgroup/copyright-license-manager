"""Utilities for parsing and handling commandline arguments"""

import argparse
import logging
from string import Formatter
from pathlib import Path
import sys
import yaml

from clmgr.__version__ import get_versions
from clmgr.template import comments, licenses, placeholders, sources, statements

log = logging.getLogger("root")

# Configuration options without a usable default
REQUIRED_OPTIONS = ["source", "legal"]

# Properties every entry of the legal option must define
REQUIRED_LEGAL_PROPERTIES = ["inception", "name", "locality", "country"]

DEFAULT_FORMAT = (
    "SPDX-FileCopyrightText: Copyright (c) {inception} - {year} "
    "[{name} - {locality} - {country}]"
)


def positive_int(value):
    """Parse a commandline value that must be a whole number of at least 1"""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"must be a whole number, got '{value}'")
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return number


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
        help="Number of lines the header must start in, after a shebang or other "
        "lines that stay on top; default=10",
        type=positive_int,
        default=10,
        metavar="REGION",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        help="Report which files would change without writing them",
        action="store_true",
    )
    parser.add_argument(
        "--check",
        help="Implies --dry-run; exit with 1 when a file would change",
        action="store_true",
    )
    parser.add_argument(
        "--diff",
        help="Print a unified diff for every file that is changed",
        action="store_true",
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
        rendering_errors = validate_legal(cfg["legal"])
        rendering_errors += validate_format(cfg.get("format"))
        errors.extend(rendering_errors)

        # The copyright statements can only be rendered from a valid format
        # and complete legal entities, the license content is always checked
        errors.extend(validate_markup(cfg, check_copyright=not rendering_errors))

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

    # A placeholder without a name, such as {}, has an empty name
    used = [
        name.split(".")[0].split("[")[0]
        for _, name, _, _ in Formatter().parse(copyright_format)
        if name is not None
    ]

    errors = []

    # Existing copyright statements are recognised by this word, without it
    # every run would add the statements again
    if "Copyright" not in copyright_format:
        errors.append("format must contain the word 'Copyright'")

    return errors + [
        (
            f"format uses unknown placeholder '{name}', "
            if name
            else "format uses a placeholder without a name '{}', "
        )
        + f"available are: {', '.join(placeholders)}"
        for name in used
        if name not in placeholders
    ]


def validate_markup(cfg, check_copyright=True):
    """Verify that the header text can be written into a markup comment

    A markup comment such as <!-- --> must not contain "--", so neither the
    copyright statements nor the license content may contain it when a markup
    source is configured.

    Parameters
    ----------
    cfg
        Parsed configuration
    check_copyright
        Whether to check the copyright statements, which requires a valid
        format and complete legal entities to render them

    Returns
    -------
        The problems found

    """
    # Unsupported sources are reported by validate_source
    markup = [
        ext for ext in cfg["source"] if ext in sources and comments[ext]["markup"]
    ]
    if not markup:
        return []

    errors = []
    # The configuration is validated before its defaults are filled in
    copyright_format = cfg.get("format") or DEFAULT_FORMAT
    legal = cfg["legal"] if check_copyright else []
    # A year never contains "--", so any year will do
    for idx, statement in enumerate(statements(copyright_format, legal, 0)):
        if "--" in statement:
            errors.append(
                f"copyright of legal entity [{idx}] contains '--', "
                f"which is not allowed in {', '.join(markup)} comments"
            )

    # The content is only written when the license is enabled and not external
    license_cfg = cfg.get("license")
    written = (
        isinstance(license_cfg, dict)
        and license_cfg.get("enabled")
        and not license_cfg.get("external")
    )
    if written and "--" in str(license_cfg.get("content", "")):
        errors.append(
            f"license content contains '--', "
            f"which is not allowed in {', '.join(markup)} comments"
        )

    return errors


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
        cfg["format"] = DEFAULT_FORMAT

    return cfg

"""Regression tests for headers that are not in the comment style of new headers"""

import datetime

from clmgr.args import apply_config_defaults, parse_args
from clmgr.processor import analyze

YEAR = datetime.datetime.now().year
SPDX = f"SPDX-FileCopyrightText: Copyright (c) 2015 - {YEAR} [Enovation Group B.V. - Capelle aan den IJssel - NL]"


def run(ext, text):
    """Analyze a file twice, the second run must not change anything"""
    cfg = apply_config_defaults(
        {
            "source": [ext],
            "legal": [
                {
                    "inception": 2015,
                    "name": "Enovation Group B.V.",
                    "locality": "Capelle aan den IJssel",
                    "country": "NL",
                }
            ],
            "license": {"enabled": True},
        }
    )
    args = parse_args([])

    action, new_lines = analyze(cfg, ext, text.splitlines(True), "file", args)
    again, _ = analyze(cfg, ext, new_lines, "file", args)
    assert again == "none"

    return action, "".join(new_lines)


def test_plain_block_header_is_updated_in_place():
    action, text = run("css", "/*\n * Copyright (c) 2015 Enovation\n */\n.a {}\n")

    assert action == "update"
    assert text == (
        f"/*\n * {SPDX}\n * ---\n * All rights reserved.\n * ---\n */\n.a {{}}\n"
    )


def test_block_comment_without_copyright_is_not_the_header():
    action, text = run("js", "/* eslint-disable */\nfoo();\n")

    assert action == "add"
    assert text.startswith("/*! ****")
    assert text.endswith(" */\n/* eslint-disable */\nfoo();\n")


def test_sass_block_header_is_updated_in_place():
    action, text = run("sass", "/* Copyright (c) 2015 Enovation */\n.a\n  b: c\n")

    assert action == "update"
    assert text == (
        f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n*/\n.a\n  b: c\n"
    )


def test_sass_block_header_ends_at_first_line_not_indented():
    action, text = run(
        "sass", "/* Copyright (c) 2015 Enovation\n   more\n.a\n  b: c\n/* later */\n"
    )

    assert action == "update"
    assert text == (
        f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n"
        "   more\n.a\n  b: c\n/* later */\n"
    )


def test_single_line_comment_is_extended():
    action, text = run("html", "<!-- build stamp -->\n<!DOCTYPE html>\n<html>\n")

    assert action == "add"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n  build stamp\n-->\n"
        "<!DOCTYPE html>\n<html>\n"
    )


def test_single_line_header_is_updated():
    action, text = run("html", "<!-- Copyright (c) 2015 Enovation -->\n<div></div>\n")

    assert action == "update"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n<div></div>\n"
    )


def test_single_line_header_is_updated_java():
    action, text = run("java", "/* Copyright (c) 2015 Enovation */ class A {}\n")

    assert action == "update"
    assert text == (
        f"/*\n * {SPDX}\n *\n * ---\n * All rights reserved.\n * ---\n */\n"
        "class A {}\n"
    )


def test_separator_is_not_a_license_marker():
    action, text = run(
        "html", "<!--\n  Copyright (c) 2015 Enovation\n  =====\n-->\n<div></div>\n"
    )

    assert action == "update"
    assert "  ===\n  All rights reserved.\n  ===\n" in text


def test_byte_order_mark_stays_in_front():
    action, text = run("html", "﻿<!DOCTYPE html>\n<html>\n")

    assert action == "add"
    assert text.startswith("﻿<!DOCTYPE html>\n<!--\n")


def test_byte_order_mark_stays_in_front_dotnet():
    action, text = run("cs", "﻿using System;\n")

    assert action == "add"
    assert text.startswith("﻿/****")
    assert text.count("﻿") == 1


def test_start_line_without_text_is_left_alone():
    text = f"/*   \n * {SPDX}\n *\n * ---\n * All rights reserved.\n * ---\n */\nclass A {{}}\n"

    action, new_text = run("java", text)

    assert action == "none"
    assert new_text == text

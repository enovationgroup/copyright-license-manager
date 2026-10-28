"""Regression tests for existing headers and leading comments in unusual layouts"""

import datetime

from clmgr.args import apply_config_defaults, parse_args
from clmgr.processor import analyze

YEAR = datetime.datetime.now().year
WARNING = "a copyright statement outside the header is left unchanged"
SPDX = f"SPDX-FileCopyrightText: Copyright (c) 2015 - {YEAR} [Enovation Group B.V. - Capelle aan den IJssel - NL]"


LEGAL = [
    {
        "inception": 2015,
        "name": "Enovation Group B.V.",
        "locality": "Capelle aan den IJssel",
        "country": "NL",
    }
]

# Entities the copyright was transferred between, the last one holds it now
TRANSFERS = [
    {"inception": year, "name": name, "locality": "Rotterdam", "country": "NL"}
    for year, name in [
        (2005, "Mars Hospital"),
        (2008, "Lunar Base"),
        (2010, "Orbit Clinic"),
        (2012, "Comet Care"),
    ]
] + LEGAL


def run(ext, text, legal=None, license=None):
    """Analyze a file twice, the second run must not change anything"""
    cfg = apply_config_defaults(
        {
            "source": [ext],
            "legal": legal or LEGAL,
            "license": license or {"enabled": True},
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
        f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n  */\n.a\n  b: c\n"
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


def test_markup_comment_without_copyright_is_left_alone():
    action, text = run("html", "<!-- build stamp -->\n<!DOCTYPE html>\n<html>\n")

    assert action == "add"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n"
        "<!-- build stamp -->\n<!DOCTYPE html>\n<html>\n"
    )


def test_markup_directive_is_left_alone():
    source = (
        "<!-- eslint-disable vue/multi-word-component-names -->\n"
        "<template>\n  <p>x</p>\n</template>\n"
    )

    action, text = run("vue", source)

    assert action == "add"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n" + source
    )


def test_markup_conditional_comment_is_left_alone():
    source = (
        '<!--[if IE]><link rel="stylesheet" href="ie.css"><![endif]-->\n<div></div>\n'
    )

    action, text = run("html", source)

    assert action == "add"
    assert text.endswith("-->\n" + source)


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


def test_copyright_on_closing_line_is_updated():
    action, text = run("css", "/*\n * note\n * Copyright (c) 2015 Enovation */ .a {}\n")

    assert action == "update"
    assert text == (
        f"/*\n * {SPDX}\n * ---\n * All rights reserved.\n * ---\n * note\n*/\n.a {{}}\n"
    )


def test_copyright_on_closing_line_is_updated_html():
    action, text = run(
        "html", "<!--\n  note\n  Copyright (c) 2015 Enovation -->\n<div></div>\n"
    )

    assert action == "update"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n  note\n-->\n"
        "<div></div>\n"
    )


def test_copyright_on_first_line_of_line_comments():
    action, text = run("py", "# Copyright (c) 2015 Enovation\n# note\nprint(1)\n")

    assert action == "update"
    assert text == f"# {SPDX}\n# ---\n# All rights reserved.\n# ---\n# note\nprint(1)\n"


def test_copyright_as_only_line_of_line_comments():
    action, text = run("py", "# Copyright (c) 2015 Enovation\nprint(1)\n")

    assert action == "update"
    assert text == f"# {SPDX}\n# ---\n# All rights reserved.\n# ---\nprint(1)\n"


def test_copyright_as_only_line_of_line_comments_sass():
    action, text = run("sass", "// Copyright (c) 2015 Enovation\n.a\n  b: c\n")

    assert action == "update"
    assert text == (f"// {SPDX}\n// ---\n// All rights reserved.\n// ---\n.a\n  b: c\n")


def test_copyright_below_first_comment_is_reported(caplog):
    action, text = run(
        "js", "/* eslint-disable */\n/* Copyright (c) 2015 Enovation */\nfoo();\n"
    )

    assert action == "add"
    assert WARNING in caplog.text


def test_first_comment_without_copyright_below_is_not_reported(caplog):
    action, _ = run("js", "/* eslint-disable */\nfoo('Copyright');\n")

    assert action == "add"
    assert WARNING not in caplog.text


def test_more_legal_entities_than_copyright_lines_keep_the_license():
    """The license moves down past the end of the header as it was before"""
    action, text = run(
        "java",
        "/*\n * Copyright (c) 2015 Enovation\n *\n * ---\n * All rights reserved.\n"
        " * ---\n */\nclass A {}\n",
        TRANSFERS,
    )

    assert action == "update"
    assert text == (
        "/*\n"
        " * SPDX-FileCopyrightText: Copyright (c) 2005 - 2008 [Mars Hospital - Rotterdam - NL]\n"
        " * SPDX-FileCopyrightText: Copyright (c) 2008 - 2010 [Lunar Base - Rotterdam - NL]\n"
        " * SPDX-FileCopyrightText: Copyright (c) 2010 - 2012 [Orbit Clinic - Rotterdam - NL]\n"
        " * SPDX-FileCopyrightText: Copyright (c) 2012 - 2015 [Comet Care - Rotterdam - NL]\n"
        f" * {SPDX}\n"
        " *\n * ---\n * All rights reserved.\n * ---\n */\nclass A {}\n"
    )


def test_fewer_legal_entities_than_copyright_lines_add_the_license():
    """The code below the header moves up into the header as it was before"""
    action, text = run(
        "html",
        "<!--\n  Copyright (c) 2010 Mars Hospital\n  Copyright (c) 2012 Lunar Base\n"
        "  Copyright (c) 2015 Enovation\n-->\n<pre>\n===\n</pre>\n",
    )

    assert action == "update"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n"
        "<pre>\n===\n</pre>\n"
    )


def test_text_starting_with_a_star_is_kept():
    action, text = run(
        "java",
        "/* *Important* note\n * Copyright (c) 2015 Enovation\n */\nclass A {}\n",
    )

    assert action == "update"
    assert text == (
        f"/*\n * {SPDX}\n *\n * ---\n * All rights reserved.\n * ---\n"
        " * *Important* note\n */\nclass A {}\n"
    )


def test_text_starting_with_an_exclamation_mark_is_kept():
    action, text = run(
        "html",
        "<!-- !Important note\n  Copyright (c) 2015 Enovation\n-->\n<div></div>\n",
    )

    assert action == "update"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n"
        "  !Important note\n-->\n<div></div>\n"
    )


def test_marker_of_a_doc_comment_is_kept():
    action, text = run(
        "java", "/** Copyright (c) 2015 Enovation\n * note\n */\nclass A {}\n"
    )

    assert action == "update"
    assert text.startswith(f"/**\n * {SPDX}\n")


def test_rule_of_stars_on_the_first_line_is_kept():
    action, text = run(
        "cs",
        "/*! *****************\n * Copyright (c) 2015 Enovation\n */\nclass A {}\n",
    )

    assert action == "update"
    assert text.startswith(f"/*! *****************\n * {SPDX}\n")


def test_decorated_header_that_is_up_to_date_is_left_alone():
    text = f"/*-------------\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n-------------*/\nselect 1;\n"

    action, new_text = run("sql", text)

    assert action == "none"
    assert new_text == text


def test_decoration_after_the_start_marker_is_kept():
    action, text = run(
        "java",
        "/*-\n * Copyright (c) 2015 Enovation\n */\nclass A {}\n",
        license={"enabled": False},
    )

    assert action == "update"
    assert text == f"/*-\n * {SPDX}\n */\nclass A {{}}\n"


def test_decoration_before_the_end_marker_is_kept():
    action, text = run(
        "sql",
        "/*=====\n  Copyright (c) 2015 Enovation\n=====*/ select 1;\n",
        license={"enabled": False},
    )

    assert action == "update"
    assert text == f"/*=====\n  {SPDX}\n=====*/\nselect 1;\n"


def test_rule_of_stars_before_the_end_marker_is_kept():
    action, text = run(
        "java",
        "/*\n * Copyright (c) 2015 Enovation\n **/ class A {}\n",
        license={"enabled": False},
    )

    assert action == "update"
    assert text == f"/*\n * {SPDX}\n **/\nclass A {{}}\n"


def test_empty_comment_becomes_the_header():
    action, text = run("java", "/**/\nclass A {}\n", license={"enabled": False})

    assert action == "add"
    assert text == f"/*\n * {SPDX}\n *\n */\nclass A {{}}\n"


def test_python_shebang_and_encoding_stay_on_top():
    action, text = run(
        "py", "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nprint(1)\n"
    )

    assert action == "add"
    assert text == (
        "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n"
        f"#\n# {SPDX}\n# ---\n# All rights reserved.\n# ---\n#\nprint(1)\n"
    )


def test_python_header_below_shebang_is_updated():
    action, text = run(
        "py", "#!/usr/bin/env python\n#\n# Copyright (c) 2015 Enovation\n#\nprint(1)\n"
    )

    assert action == "update"
    assert text == (
        "#!/usr/bin/env python\n"
        f"#\n# {SPDX}\n# ---\n# All rights reserved.\n# ---\n#\nprint(1)\n"
    )


def test_sass_closing_line_is_written_indented():
    action, text = run(
        "sass", "/*\n  note\n  Copyright (c) 2015 Enovation */\n.a\n  b: c\n"
    )

    assert action == "update"
    assert text == (
        f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n  note\n  */\n"
        ".a\n  b: c\n"
    )


BANNER_START = "/*! " + "*" * 77 + "\n"
BANNER_END = "*" * 78 + " */\n"


def test_external_license_is_added_inside_the_header():
    action, text = run(
        "js",
        BANNER_START + f"{SPDX}\n" + BANNER_END + "const a = 1;\n",
        license={"enabled": True, "external": True},
    )

    assert action == "update"
    assert text == BANNER_START + f"{SPDX}\n---\n---\n" + BANNER_END + "const a = 1;\n"


def test_external_license_is_added_inside_the_header_java():
    action, text = run(
        "java",
        "/*\n * Copyright (c) 2015 Enovation\n */\nclass A {}\n",
        license={"enabled": True, "external": True},
    )

    assert action == "update"
    assert text == f"/*\n * {SPDX}\n *\n * ---\n * ---\n */\nclass A {{}}\n"


MULTI_LINE_LICENSE = {
    "enabled": True,
    "content": "Licensed under the MIT License.\n\nSee LICENSE for details.\n",
}


def test_multi_line_license_stays_inside_line_comments():
    action, text = run("sass", ".a\n  b: c\n", license=MULTI_LINE_LICENSE)

    assert action == "add"
    assert text == (
        f"//\n// {SPDX}\n// ---\n// Licensed under the MIT License.\n//\n"
        "// See LICENSE for details.\n// ---\n//\n.a\n  b: c\n"
    )


def test_multi_line_license_is_added_to_an_existing_header():
    action, text = run(
        "py",
        "#\n# Copyright (c) 2015 Enovation\n#\nprint(1)\n",
        license=MULTI_LINE_LICENSE,
    )

    assert action == "update"
    assert text == (
        f"#\n# {SPDX}\n# ---\n# Licensed under the MIT License.\n#\n"
        "# See LICENSE for details.\n# ---\n#\nprint(1)\n"
    )


def test_multi_line_license_in_a_block_comment():
    action, text = run("java", "class A {}\n", license=MULTI_LINE_LICENSE)

    assert action == "add"
    assert text == (
        f"/*\n * {SPDX}\n *\n * ---\n * Licensed under the MIT License.\n *\n"
        " * See LICENSE for details.\n * ---\n *\n */\nclass A {}\n"
    )


def test_comment_beyond_the_search_region_is_not_the_header():
    source = "\n" * 12 + "<!--\n  Copyright 2019 X\n-->\n<div></div>\n"

    action, text = run("html", source)

    assert action == "add"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n" + source
    )


def test_legacy_header_is_updated_without_a_divider():
    action, text = run("cs", "/* Copyright (c) 2010 Old */\nclass A {}\n")

    assert action == "update"
    assert text == (
        f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n*/\nclass A {{}}\n"
    )


def test_copyright_below_first_comment_is_reported_java(caplog):
    action, text = run(
        "java", "/* eslint-disable */\n/* Copyright (c) 2015 Enovation */\nclass A {}\n"
    )

    assert action == "add"
    assert text.endswith(
        " * eslint-disable\n */\n/* Copyright (c) 2015 Enovation */\nclass A {}\n"
    )
    assert WARNING in caplog.text


def test_plain_block_header_is_updated_in_place_typescript():
    action, text = run("ts", "/* Copyright (c) 2015 Enovation */\nlet a;\n")

    assert action == "update"
    assert text == f"/*\n  {SPDX}\n  ---\n  All rights reserved.\n  ---\n*/\nlet a;\n"


def test_header_closed_at_the_start_of_a_line_ends_there():
    code = (
        "class Writer {\n"
        "    void close(java.io.PrintWriter out) {\n"
        '        out.println(" */");\n'
        "    }\n"
        "}\n"
    )

    action, text = run("java", "/*\n Copyright (c) 2010 Old\n*/\n" + code)

    assert action == "update"
    assert text == f"/*\n {SPDX}\n\n ---\n All rights reserved.\n ---\n*/\n" + code


def test_header_closed_without_a_space_ends_there_dotnet():
    code = "class A {\n    /** x */\n    int a;\n}\n"

    action, text = run(
        "cs", "/" + "*" * 73 + "\n * Copyright (c) 2010 Old\n **/\n" + code
    )

    assert action == "update"
    assert text.endswith(" **/\n" + code)


def test_sass_directive_is_left_alone():
    source = (
        "// stylelint-disable-next-line scss/dollar-variable-pattern\n$Bad_Name: 1\n"
    )

    action, text = run("sass", source)

    assert action == "add"
    assert text == (
        f"//\n// {SPDX}\n// ---\n// All rights reserved.\n// ---\n//\n\n" + source
    )


def test_sass_line_comment_header_is_updated():
    action, text = run(
        "sass", "//\n// Copyright (c) 2015 Enovation\n// note\n//\n.a\n  b: c\n"
    )

    assert action == "update"
    assert text == (
        f"//\n// {SPDX}\n// ---\n// All rights reserved.\n// ---\n// note\n//\n.a\n  b: c\n"
    )


def test_line_with_only_the_comment_char_does_not_set_the_prefix():
    action, text = run("ts", "/*\n *\n * Copyright (c) 2010 Old\n *\n */\nx();\n")

    assert action == "update"
    assert text == (
        f"/*\n * {SPDX}\n * ---\n * All rights reserved.\n * ---\n *\n *\n */\nx();\n"
    )


def test_line_with_only_the_comment_char_does_not_set_the_prefix_java():
    action, text = run("java", "/*\n *\n * Copyright (c) 2010 Old\n */\nclass A {}\n")

    assert action == "update"
    assert f" * {SPDX}\n" in text


def test_markup_directive_followed_by_a_copyright_comment_on_one_line():
    source = "<!-- a --><!-- Copyright (c) 2010 Old -->\n<template></template>\n"

    action, text = run("vue", source)

    assert action == "add"
    assert text == (
        f"<!--\n  {SPDX}\n  ===\n  All rights reserved.\n  ===\n-->\n" + source
    )


def test_copyright_in_a_later_comment_is_reported(caplog):
    run(
        "js",
        "/* eslint-disable */\n/* jshint esversion: 6 */\n/* Copyright (c) 2015 X */\n"
        "foo();\n",
    )

    assert f'{WARNING}: "/* Copyright (c) 2015 X */"' in caplog.text


def test_copyright_in_a_comment_after_code_is_reported(caplog):
    run("js", '/* eslint-disable */\nimport a from "a";\n/* Copyright (c) 2015 X */\n')

    assert f'{WARNING}: "/* Copyright (c) 2015 X */"' in caplog.text


def test_copyright_in_a_line_comment_is_reported(caplog):
    action, text = run("ts", "// Copyright (c) 2015 X\nfoo();\n")

    assert action == "add"
    assert text.endswith(" */\n// Copyright (c) 2015 X\nfoo();\n")
    assert f'{WARNING}: "// Copyright (c) 2015 X"' in caplog.text


def test_copyright_in_a_line_comment_is_reported_sql(caplog):
    run(
        "sql",
        "/*\n  Copyright (c) 2015 Enovation\n*/\n-- Copyright (c) 2010 X\nSELECT 1;\n",
    )

    assert f'{WARNING}: "-- Copyright (c) 2010 X"' in caplog.text


def test_copyright_in_a_script_comment_is_reported(caplog):
    action, text = run(
        "vue",
        '<script setup lang="ts">\n/*\n * Copyright (c) 2019 X\n */\n'
        "// Copyright (c) 2020 Y\n</script>\n",
    )

    assert action == "add"
    assert "-->\n<script setup" in text
    assert f'{WARNING}: "* Copyright (c) 2019 X"' in caplog.text
    assert f'{WARNING}: "// Copyright (c) 2020 Y"' in caplog.text


def test_copyright_in_a_style_comment_is_reported(caplog):
    run("html", "<style>\n  /* Copyright (c) 2019 X */\n</style>\n")

    assert f'{WARNING}: "/* Copyright (c) 2019 X */"' in caplog.text


def test_copyright_outside_an_updated_header_is_reported(caplog):
    action, _ = run(
        "java",
        "/*\n * Copyright (c) 2015 Enovation\n */\n// Copyright (c) 2010 X\nclass A {}\n",
    )

    assert action == "update"
    assert f'{WARNING}: "// Copyright (c) 2010 X"' in caplog.text


def test_copyright_on_the_line_of_another_comment_is_reported(caplog):
    run("vue", "<!-- a --><!-- Copyright (c) 2010 X -->\n<template></template>\n")

    assert WARNING in caplog.text


def test_comments_without_copyright_are_not_reported(caplog):
    run("java", "/* a */\n/* b */\n// c\nclass A {}\n")

    assert WARNING not in caplog.text


def test_copyright_beyond_the_search_region_is_not_reported(caplog):
    run("js", "foo();\n" * 12 + "// Copyright (c) 2010 X\n")

    assert WARNING not in caplog.text

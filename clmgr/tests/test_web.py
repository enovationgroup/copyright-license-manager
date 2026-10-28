import pytest

from clmgr.args import apply_config_defaults, parse_args
from clmgr.template import comments
from clmgr.processor import analyze, count_prologue_lines
from clmgr.tests.test_base import run_test_config


def test_prologue_shebang_javascript():
    run_test_config("default/js/", "prologue.js", "default/single.yml")


def test_prologue_charset_css():
    run_test_config("default/css/", "prologue.css", "default/single.yml")


def test_prologue_charset_sass():
    run_test_config("default/sass/", "prologue.sass", "default/single.yml")


def test_prologue_doctype_html():
    run_test_config("default/html/", "prologue.html", "default/single.yml")


def test_prologue_doctype_html_update():
    run_test_config(
        "default/html/", "prologue-update.html", "default/single.update.yml"
    )


def test_prologue_xml_declaration_html():
    run_test_config("default/html/", "prologue-xml.html", "default/single.yml")


# Extensions that share their comment style with a fully tested extension
SHARED_STYLE_EXTENSIONS = ["mjs", "cjs", "jsx", "tsx", "less", "htm", "vue", "svelte"]


@pytest.mark.parametrize("ext", SHARED_STYLE_EXTENSIONS)
def test_single_extensions(ext):
    run_test_config(f"default/{ext}/", f"single.{ext}", "default/single.yml")


@pytest.mark.parametrize("ext", SHARED_STYLE_EXTENSIONS)
def test_single_update_extensions(ext):
    run_test_config(
        f"default/{ext}/", f"single-update.{ext}", "default/single.update.yml"
    )


def test_prologue_without_prologue():
    lines = ["<div>\n", "</div>\n"]

    assert count_prologue_lines(lines, comments["html"]["prologue"]) == 0


def test_prologue_not_configured():
    lines = ["#!/usr/bin/env dotnet\n", "using System;\n"]

    assert count_prologue_lines(lines, comments["cs"]["prologue"]) == 0


def test_prologue_python_shebang_and_encoding():
    lines = ["#!/usr/bin/env python\n", "# -*- coding: utf-8 -*-\n", "# note\n"]

    assert count_prologue_lines(lines, comments["py"]["prologue"]) == 2


def test_prologue_python_encoding_without_shebang():
    lines = ["# vim: set fileencoding=utf-8 :\n", "print('test')\n"]

    assert count_prologue_lines(lines, comments["py"]["prologue"]) == 1


def test_prologue_python_comment_is_not_an_encoding():
    lines = ["# Copyright (c) 2015 Enovation\n", "print('test')\n"]

    assert count_prologue_lines(lines, comments["py"]["prologue"]) == 0


def test_prologue_doctype_after_blank_line():
    lines = ["\n", "<!DOCTYPE html>\n", "<html>\n"]

    assert count_prologue_lines(lines, comments["html"]["prologue"]) == 2


def test_prologue_only_at_start_of_file():
    lines = ["\n", "#!/usr/bin/env node\n", "foo();\n"]

    assert count_prologue_lines(lines, comments["js"]["prologue"]) == 0


def test_prologue_matched_once():
    lines = ['@charset "UTF-8";\n', '@charset "UTF-8";\n', ".a {}\n"]

    assert count_prologue_lines(lines, comments["css"]["prologue"]) == 1


def test_prologue_multi_line_doctype():
    lines = [
        '<?xml version="1.0"?>\n',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n',
        '    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n',
        "<html>\n",
    ]

    assert count_prologue_lines(lines, comments["html"]["prologue"]) == 3


def test_prologue_without_line_ending():
    lines = ["<!DOCTYPE html>"]

    assert count_prologue_lines(lines, comments["html"]["prologue"]) == 1


def test_prologue_without_line_ending_keeps_header_on_own_line():
    cfg = apply_config_defaults(
        {
            "source": ["html"],
            "legal": [
                {
                    "inception": 2015,
                    "name": "Enovation Group B.V.",
                    "locality": "Capelle aan den IJssel",
                    "country": "NL",
                }
            ],
        }
    )
    args = parse_args([])

    action, new_lines = analyze(cfg, "html", ["<!DOCTYPE html>"], "test.html", args)

    assert action == "add"
    assert new_lines[0] == "<!DOCTYPE html>\n"
    assert new_lines[1] == "<!--\n"


def test_comment_styles_have_the_same_shape():
    keys = set(comments["java"])

    for ext, comment in comments.items():
        assert set(comment) == keys, ext


def test_comment_styles_do_not_share_state():
    styles = list(comments.values())

    for idx, comment in enumerate(styles):
        for other in styles[idx + 1 :]:
            assert comment is not other
            assert comment["license"] is not other["license"]
            assert comment["prologue"] is not other["prologue"]
            assert comment["legacy"] is not other["legacy"]
            for legacy in comment["legacy"]:
                assert all(legacy is not shared for shared in other["legacy"])


def test_markup_styles():
    markup = {ext for ext, comment in comments.items() if comment["markup"]}

    assert markup == {"html", "htm", "vue", "svelte"}


def test_prologue_shebang_for_every_script_extension():
    lines = ["#!/usr/bin/env bun\n", "console.log('test');\n"]

    for ext in ["ts", "js", "mjs", "cjs", "jsx", "tsx"]:
        assert count_prologue_lines(lines, comments[ext]["prologue"]) == 1, ext

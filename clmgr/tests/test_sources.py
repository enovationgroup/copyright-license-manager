"""Which files clmgr processes, and in which comment style"""

import os
import sys

import pytest
import yaml

from clmgr.main import main
from clmgr.paths import comment_extension, interpreter
from clmgr.template import comments, sources, types

LEGAL = [
    {
        "inception": 2015,
        "name": "Enovation Group B.V.",
        "locality": "Capelle aan den IJssel",
        "country": "NL",
    }
]

COPYRIGHT = b"SPDX-FileCopyrightText"


def run_tree(tmp_path, source, files, *extra_args, options=None):
    """Run clmgr on a directory holding the given files

    The directory is tmp_path/project. Returns the exit code and the contents
    of every file after the run.
    """
    project = tmp_path / "project"
    for name, data in files.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    config = tmp_path / "copyright.yml"
    content = {"source": source, "legal": LEGAL, **(options or {})}
    config.write_text(yaml.safe_dump(content), "utf-8")

    code = main(["-c", str(config), "-d", str(project)] + list(extra_args))

    return code, {name: (project / name).read_bytes() for name in files}


def test_file_that_is_not_utf8_is_skipped(tmp_path, caplog):
    latin = "print('café')\n".encode("latin-1")

    code, files = run_tree(
        tmp_path, ["py"], {"a_latin.py": latin, "b_good.py": b"print(1)\n"}
    )

    assert code == 0
    assert files["a_latin.py"] == latin
    assert COPYRIGHT in files["b_good.py"]
    assert "a_latin.py, it is not UTF-8 encoded" in caplog.text


BANNER = b"/*! ****"
MARKUP = b"<!--\n"
HASH = b"#\n# SPDX"


def test_type_selects_its_extensions_regardless_of_case(tmp_path):
    code, files = run_tree(
        tmp_path,
        [{"type": "javascript"}],
        {"a.js": b"a();\n", "b.MJS": b"b();\n", "c.cjs": b"c();\n", "d.ts": b"d();\n"},
    )

    assert code == 0
    assert all(files[name].startswith(BANNER) for name in ["a.js", "b.MJS", "c.cjs"])
    assert files["d.ts"] == b"d();\n"


def test_plain_extension_keeps_its_meaning(tmp_path):
    _, files = run_tree(tmp_path, ["ts"], {"a.ts": b"a();\n", "b.tsx": b"b();\n"})

    assert files["a.ts"].startswith(BANNER)
    assert files["b.tsx"] == b"b();\n"


def test_include_adds_files_to_a_type(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "python", "include": ["bin/*"], "exclude": ["bin/*.*"]}],
        {
            "bin/tool": b"print(1)\n",
            "bin/README.md": b"Tools\n",
            "src/a.py": b"print(2)\n",
        },
    )

    assert files["bin/tool"].startswith(HASH)
    assert files["bin/README.md"] == b"Tools\n"
    assert files["src/a.py"].startswith(HASH)


def test_exclude_only_narrows_its_own_type(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "javascript", "exclude": ["legacy/*"]}, {"type": "stylesheet"}],
        {"legacy/a.js": b"a();\n", "legacy/b.css": b".b {}\n", "c.js": b"c();\n"},
    )

    assert files["legacy/a.js"] == b"a();\n"
    assert files["legacy/b.css"].startswith(BANNER)
    assert files["c.js"].startswith(BANNER)


def test_plain_extension_is_not_narrowed_by_a_type(tmp_path):
    _, files = run_tree(
        tmp_path,
        ["js", {"type": "javascript", "exclude": ["legacy/*"]}],
        {"legacy/a.js": b"a();\n"},
    )

    assert files["legacy/a.js"].startswith(BANNER)


def test_pattern_takes_precedence_over_the_extension(tmp_path):
    """Qt Linguist translations are XML files with the extension ts"""
    _, files = run_tree(
        tmp_path,
        [{"type": "typescript"}, {"type": "markup", "include": ["translations/*"]}],
        {"translations/app.ts": b"<TS></TS>\n", "src/app.ts": b"app();\n"},
    )

    assert files["translations/app.ts"].startswith(MARKUP)
    assert files["src/app.ts"].startswith(BANNER)


def test_top_level_exclude_applies_to_included_files(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "python", "include": ["bin/*"]}],
        {"bin/tool": b"print(1)\n", "bin/old": b"print(2)\n"},
        options={"exclude": ["bin/old"]},
    )

    assert files["bin/tool"].startswith(HASH)
    assert files["bin/old"] == b"print(2)\n"


def test_file_included_by_two_types_is_an_error(tmp_path, caplog):
    source = [
        {"type": "python", "include": ["bin/*"]},
        {"type": "sql", "include": ["bin/*"]},
    ]
    files = {"bin/tool": b"print(1)\n", "bin/other": b"other\n"}

    with pytest.raises(SystemExit) as excinfo:
        run_tree(tmp_path, source, files)

    assert excinfo.value.code == 2
    assert "bin/other is included by the types python and sql" in caplog.text
    assert "bin/tool is included by the types python and sql" in caplog.text
    assert (tmp_path / "project/bin/tool").read_bytes() == b"print(1)\n"


def test_single_file_follows_the_same_rules(tmp_path):
    tool = tmp_path / "project/bin/tool"

    code, files = run_tree(
        tmp_path,
        [{"type": "python", "include": ["bin/*"]}],
        {"bin/tool": b"print(1)\n", "bin/other": b"print(2)\n"},
        "--file",
        str(tool),
    )

    assert code == 0
    assert files["bin/tool"].startswith(HASH)
    assert files["bin/other"] == b"print(2)\n"


def test_single_file_that_an_exclude_pattern_takes_out_is_skipped(tmp_path, caplog):
    code, files = run_tree(
        tmp_path,
        ["py"],
        {"vendor/a.py": b"print(1)\n"},
        "--file",
        str(tmp_path / "project/vendor/a.py"),
        options={"exclude": ["vendor"]},
    )

    assert code == 0
    assert files["vendor/a.py"] == b"print(1)\n"
    assert "Skipping vendor/a.py, an exclude pattern takes it out" in caplog.text


def test_single_file_outside_the_include_patterns_is_skipped(tmp_path, caplog):
    code, files = run_tree(
        tmp_path,
        ["py"],
        {"lib/a.py": b"print(1)\n"},
        "--file",
        str(tmp_path / "project/lib/a.py"),
        options={"include": ["src/**/*"]},
    )

    assert code == 0
    assert files["lib/a.py"] == b"print(1)\n"
    assert "Skipping lib/a.py, the include patterns do not select it" in caplog.text


def test_single_file_in_an_installed_package_is_skipped(tmp_path, caplog):
    code, files = run_tree(
        tmp_path,
        ["js"],
        {"node_modules/lodash/lodash.js": b"a();\n"},
        "--file",
        str(tmp_path / "project/node_modules/lodash/lodash.js"),
        options={"include": ["**/*"]},
    )

    assert code == 0
    assert files["node_modules/lodash/lodash.js"] == b"a();\n"
    assert "lodash.js, it is in node_modules" in caplog.text


def test_every_extension_belongs_to_one_type():
    extensions = [
        ext for file_type in types.values() for ext in file_type["extensions"]
    ]

    assert sorted(extensions) == sorted(sources)


@pytest.mark.parametrize(
    "first_line, name",
    [
        (b"#!/usr/bin/perl5.36\n", "perl"),
        (b"#!/usr/bin/env perl\n", "perl"),
        (b"#!/usr/bin/env -S perl -w\n", "perl"),
        (b"#! /usr/bin/python3.11\r\n", "python"),
        (b"#!/usr/bin/env PYTHONPATH=lib python3\n", "python"),
        (b"#!/usr/bin/env node\n", "node"),
        (b"#!/bin/env node\n", "node"),
        (b"#!/usr/bin/env -u PYTHONPATH python3\n", "python"),
        (b"#!/usr/bin/env -C /srv python3 -u\n", "python"),
        (b"\xef\xbb\xbf#!/usr/bin/env node\n", "node"),
        (b"#!C:\\Python39\\python.exe\r\n", "python"),
        (b"#!/usr/bin/caf\xe9\n", "caf\ufffd"),
        (b"#!\n", ""),
        (b"print(1)\n", None),
        (b"\n", None),
    ],
)
def test_interpreter_of_a_shebang(first_line, name):
    assert interpreter(first_line + b"rest\n") == name


BIN = {"include": ["bin/*"], "exclude": ["bin/*.*"]}


def test_shebang_decides_between_types_that_include_a_file(tmp_path, caplog):
    code, files = run_tree(
        tmp_path,
        [{"type": "python", **BIN}, {"type": "javascript", **BIN}],
        {
            "bin/a": b"#!/usr/bin/env python3\nprint(1)\n",
            "bin/b": b"#!/usr/bin/env node\nb();\n",
            "bin/c": b"#!/bin/bash\necho c\n",
        },
        "--debug",
    )

    assert code == 0
    assert files["bin/a"].startswith(b"#!/usr/bin/env python3\n" + HASH)
    assert files["bin/b"].startswith(b"#!/usr/bin/env node\n" + BANNER)
    assert files["bin/c"] == b"#!/bin/bash\necho c\n"
    assert "Skipping bin/c, its shebang names bash" in caplog.text


def test_shebang_of_a_type_that_does_not_include_the_file(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "sql", **BIN}, {"type": "python"}],
        {"bin/a": b"#!/usr/bin/python\nprint(1)\n"},
    )

    assert files["bin/a"].startswith(b"#!/usr/bin/python\n" + HASH)


def test_shebang_of_a_type_that_is_not_listed_skips_the_file(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "sql", **BIN}],
        {"bin/a": b"#!/usr/bin/python\nprint(1)\n"},
    )

    assert files["bin/a"] == b"#!/usr/bin/python\nprint(1)\n"


def test_include_pattern_decides_between_types_of_an_interpreter(tmp_path):
    script = tmp_path / "tool"
    script.write_bytes(b"#!/usr/bin/env bun\n")
    source = [{"type": "typescript"}, {"type": "javascript", **BIN}]

    assert comment_extension(source, "bin/tool", script) == "js"


def test_files_selected_by_extension_are_not_checked_for_a_shebang(tmp_path):
    _, files = run_tree(
        tmp_path, [{"type": "python"}], {"a.py": b"#!/usr/bin/env node\nprint(1)\n"}
    )

    assert files["a.py"].startswith(b"#!/usr/bin/env node\n" + HASH)


def test_shebang_does_not_pick_a_type_that_excludes_the_file(tmp_path):
    _, files = run_tree(
        tmp_path,
        [{"type": "python", **BIN}, {"type": "javascript", "exclude": ["bin/*"]}],
        {"bin/a": b"#!/usr/bin/env node\na();\n"},
    )

    assert files["bin/a"] == b"#!/usr/bin/env node\na();\n"


def test_plain_extension_takes_precedence_over_an_include_pattern(tmp_path):
    _, files = run_tree(
        tmp_path,
        ["py", {"type": "sql", "include": ["bin/*"]}],
        {"bin/tool.py": b"print(1)\n", "bin/query": b"select 1;\n"},
    )

    assert files["bin/tool.py"].startswith(HASH)
    assert files["bin/query"].startswith(b"/*\n")


@pytest.mark.parametrize("name", list(types))
def test_extensions_of_a_type_share_a_comment_style(name):
    """Apart from the lines that stay on top, such as a doctype in html"""
    first, *others = types[name]["extensions"]

    for ext in others:
        assert {**comments[ext], "prologue": []} == {**comments[first], "prologue": []}


def test_included_file_keeps_its_own_extension_in_the_type(tmp_path):
    """A vue component has no doctype that stays on top, as html has"""
    _, files = run_tree(
        tmp_path,
        [{"type": "markup", "include": ["components/*"]}],
        {"components/a.vue": b"<!DOCTYPE html>\n<p></p>\n"},
    )

    assert files["components/a.vue"].startswith(MARKUP)


@pytest.mark.skipif(sys.platform == "win32", reason="needs symbolic links and pipes")
def test_only_regular_files_are_selected(tmp_path):
    bin_dir = tmp_path / "project/bin"
    bin_dir.mkdir(parents=True)
    os.symlink(tmp_path / "missing", bin_dir / "broken")
    os.mkfifo(bin_dir / "pipe")

    code, files = run_tree(
        tmp_path, [{"type": "python", **BIN}], {"bin/tool": b"print(1)\n"}
    )

    assert code == 0
    assert files["bin/tool"].startswith(HASH)


def test_single_file_that_does_not_exist_is_skipped(tmp_path, caplog):
    code, _ = run_tree(
        tmp_path,
        ["py"],
        {"a.py": b"print(1)\n"},
        "--file",
        str(tmp_path / "project/missing.py"),
    )

    assert code == 0
    assert "missing.py, it is not a file" in caplog.text


def test_binary_file_that_a_type_includes_is_skipped(tmp_path):
    blob = b"\x00\x01\x02ASCII\x00"

    code, files = run_tree(
        tmp_path,
        [{"type": "python", **BIN}, {"type": "sql", **BIN}],
        {"bin/blob": blob, "bin/tool": b"#!/usr/bin/python\nprint(1)\n"},
    )

    assert code == 0
    assert files["bin/blob"] == blob
    assert files["bin/tool"].startswith(b"#!/usr/bin/python\n" + HASH)


@pytest.mark.skipif(sys.platform == "win32", reason="needs symbolic links")
def test_single_file_in_an_input_directory_given_by_a_link(tmp_path):
    project = tmp_path / "project"
    (project / "bin").mkdir(parents=True)
    (project / "bin/tool").write_bytes(b"print(1)\n")
    os.symlink(project, tmp_path / "link")
    config = tmp_path / "copyright.yml"
    config.write_text(
        yaml.safe_dump({"source": [{"type": "python", **BIN}], "legal": LEGAL}),
        "utf-8",
    )

    args = ["-c", str(config), "-d", str(tmp_path / "link")]
    assert main(args + ["--file", str(project / "bin/tool")]) == 0

    assert (project / "bin/tool").read_bytes().startswith(HASH)


def test_single_file_is_checked_for_a_shebang(tmp_path):
    code, files = run_tree(
        tmp_path,
        [{"type": "python", **BIN}, {"type": "javascript", **BIN}],
        {"bin/a": b"#!/usr/bin/env node\na();\n"},
        "--file",
        str(tmp_path / "project/bin/a"),
    )

    assert code == 0
    assert files["bin/a"].startswith(b"#!/usr/bin/env node\n" + BANNER)


def test_single_file_included_by_two_types_is_an_error(tmp_path, caplog):
    source = [{"type": "python", **BIN}, {"type": "sql", **BIN}]

    with pytest.raises(SystemExit) as excinfo:
        run_tree(
            tmp_path,
            source,
            {"bin/a": b"a\n"},
            "--file",
            str(tmp_path / "project/bin/a"),
        )

    assert excinfo.value.code == 2
    assert "bin/a is included by the types python and sql" in caplog.text

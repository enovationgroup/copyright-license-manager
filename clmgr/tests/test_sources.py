"""Which files clmgr processes, and in which comment style"""

import pytest
import yaml

from clmgr.main import main
from clmgr.template import sources, types

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


def test_every_extension_belongs_to_one_type():
    extensions = [ext for type_extensions in types.values() for ext in type_extensions]

    assert sorted(extensions) == sorted(sources)

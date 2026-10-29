"""Which files clmgr processes, and in which comment style"""

import yaml

from clmgr.main import main

LEGAL = [
    {
        "inception": 2015,
        "name": "Enovation Group B.V.",
        "locality": "Capelle aan den IJssel",
        "country": "NL",
    }
]

COPYRIGHT = b"SPDX-FileCopyrightText"


def run_tree(tmp_path, source, files, *extra_args):
    """Run clmgr on a directory holding the given files

    Returns the exit code and the contents of every file after the run.
    """
    project = tmp_path / "project"
    for name, data in files.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    config = tmp_path / "copyright.yml"
    config.write_text(yaml.safe_dump({"source": source, "legal": LEGAL}), "utf-8")

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

import shutil

import pytest

from clmgr.args import apply_config_defaults, read_config, validate_config
from clmgr.main import main
from clmgr.tests.test_base import test_dir

VALID_LEGAL = """legal:
  - inception: 2015
    name: Enovation Group B.V.
    locality: Capelle aan den IJssel
    country: NL
"""


def write_config(tmp_path, content):
    config_file = tmp_path / "copyright.yml"
    config_file.write_text(content, encoding="utf-8")

    return config_file


def run_config(tmp_path, content):
    """Run clmgr on a single source file with the given configuration"""
    config_file = write_config(tmp_path, content)
    source_file = tmp_path / "single.py"
    shutil.copy(test_dir + "/input/default/py/single.py", source_file)

    main(["-c", str(config_file), "--file", str(source_file)])


def assert_rejected(tmp_path, content, message, caplog):
    config_file = write_config(tmp_path, content)

    with pytest.raises(SystemExit) as excinfo:
        cfg = read_config(config_file)
        validate_config(cfg, config_file)

    assert excinfo.value.code == 2
    assert message in caplog.text


def test_empty_config(tmp_path, caplog):
    assert_rejected(tmp_path, "", "is empty", caplog)


def test_config_that_is_not_a_mapping(tmp_path, caplog):
    assert_rejected(tmp_path, "- a\n- b\n", "must be a mapping", caplog)


def test_malformed_config(tmp_path, caplog):
    assert_rejected(tmp_path, "source: [py\n", "Unable to parse configuration", caplog)


def test_config_without_source(tmp_path, caplog):
    assert_rejected(tmp_path, VALID_LEGAL, "missing required option 'source'", caplog)


def test_config_without_legal(tmp_path, caplog):
    assert_rejected(
        tmp_path, "source:\n  - py\n", "missing required option 'legal'", caplog
    )


def test_config_with_empty_source(tmp_path, caplog):
    assert_rejected(
        tmp_path, "source:\n" + VALID_LEGAL, "missing required option 'source'", caplog
    )


def test_config_with_unsupported_source(tmp_path, caplog):
    assert_rejected(
        tmp_path, "source:\n  - js\n" + VALID_LEGAL, "is not supported", caplog
    )


def test_config_with_incomplete_legal_entity(tmp_path, caplog):
    assert_rejected(
        tmp_path,
        "source:\n  - py\nlegal:\n  - name: Enovation Group B.V.\n",
        "legal entity [0] is missing: inception, locality, country",
        caplog,
    )


def test_config_reports_every_problem(tmp_path, caplog):
    assert_rejected(
        tmp_path,
        "source:\n  - js\nlegal:\n  - name: Enovation Group B.V.\n",
        "is not supported",
        caplog,
    )

    assert "legal entity [0] is missing" in caplog.text


def test_config_without_license_disables_the_license(tmp_path):
    """A license notice is optional, leaving it out must not fail the run"""
    run_config(tmp_path, "source:\n  - py\n" + VALID_LEGAL)

    assert "All rights reserved" not in (tmp_path / "single.py").read_text()


def test_license_without_content_uses_the_default(tmp_path):
    run_config(
        tmp_path,
        "source:\n  - py\nlicense:\n  enabled: true\n" + VALID_LEGAL,
    )

    assert "All rights reserved" in (tmp_path / "single.py").read_text()


def test_defaults_are_applied():
    cfg = apply_config_defaults({"source": ["py"], "legal": []})

    assert cfg["include"] == []
    assert cfg["exclude"] == []
    assert cfg["license"]["enabled"] is False
    assert cfg["format"].startswith("SPDX-FileCopyrightText")


def test_defaults_do_not_overwrite_configured_options():
    cfg = apply_config_defaults(
        {
            "source": ["py"],
            "legal": [],
            "include": ["src/**/*"],
            "format": "Copyright {year}",
            "license": {"enabled": True, "content": "Custom"},
        }
    )

    assert cfg["include"] == ["src/**/*"]
    assert cfg["format"] == "Copyright {year}"
    assert cfg["license"]["content"] == "Custom"
    assert cfg["license"]["external"] is False

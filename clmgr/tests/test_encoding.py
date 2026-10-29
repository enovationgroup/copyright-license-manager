"""Tests for preserving how a source file is encoded

A run may only change the copyright header. Everything else about the file has
to survive it untouched, in particular the byte order mark that Visual Studio
writes in front of C# sources and the line endings of a repository written on
Windows.
"""

import codecs
import os
import re

import pytest

from clmgr.main import main
from clmgr.tests.test_idempotent import CONFIGS, OUTPUTS, scenario

test_dir = os.path.dirname(os.path.realpath(__file__))

config_file = test_dir + "/config/default/single.yml"

# A source file per comment style: block comments (cs, sql), line comments (py)
# and markup with a doctype that stays above the header (html)
sources = {
    "cs": ["using System;", "", "namespace Demo", "{", "}"],
    "py": ["import os", "", "print(os.name)"],
    "sql": ["select 1;"],
    "html": ["<!DOCTYPE html>", "<html>", "</html>"],
}

copyright_marker = b"SPDX-FileCopyrightText"


def write_source(path, ext, newline, bom):
    """Write a source file with the given line ending, with or without a BOM"""
    body = newline.join(sources[ext]) + newline
    data = body.encode("utf-8")
    if bom:
        data = codecs.BOM_UTF8 + data

    path.write_bytes(data)

    return path


def line_endings(data):
    """The distinct line endings used in the contents of a file"""
    return set(re.findall(rb"\r\n|\r|\n", data))


def run(path, *extra_args):
    """Run clmgr on a single file and return its exit code"""
    return main(["-c", config_file, "--file", str(path)] + list(extra_args))


def assert_encoding_preserved(path, newline, bom):
    """The file carries exactly one BOM, at the front, and one line ending"""
    data = path.read_bytes()

    assert data.startswith(codecs.BOM_UTF8) is bom
    assert data.count(codecs.BOM_UTF8) == (1 if bom else 0)
    assert line_endings(data) == {newline.encode("utf-8")}


parameters = pytest.mark.parametrize(
    "ext,newline,bom",
    [
        (ext, newline, bom)
        for ext in sources
        for newline in ["\r\n", "\n"]
        for bom in [True, False]
    ],
)


@parameters
def test_insert_preserves_encoding(tmp_path, ext, newline, bom):
    source = write_source(tmp_path / f"sample.{ext}", ext, newline, bom)

    assert run(source) == 0

    assert_encoding_preserved(source, newline, bom)
    assert source.read_bytes().count(copyright_marker) == 1


@parameters
def test_update_preserves_encoding(tmp_path, ext, newline, bom):
    source = write_source(tmp_path / f"sample.{ext}", ext, newline, bom)
    run(source)

    # Age the copyright statement so the next run has to rewrite it
    stale = re.sub(
        rb"Copyright \(c\) \d{4} - \d{4}",
        b"Copyright (c) 1999 - 2000",
        source.read_bytes(),
    )
    source.write_bytes(stale)

    assert run(source) == 0

    assert_encoding_preserved(source, newline, bom)
    assert b"1999 - 2000" not in source.read_bytes()
    assert source.read_bytes().count(copyright_marker) == 1


@parameters
def test_up_to_date_file_is_left_alone(tmp_path, ext, newline, bom):
    """A second run must not touch a single byte, and must not add a header

    The existing header is found behind a BOM as well.
    """
    source = write_source(tmp_path / f"sample.{ext}", ext, newline, bom)
    run(source)
    processed = source.read_bytes()

    assert run(source) == 0

    assert source.read_bytes() == processed
    assert processed.count(copyright_marker) == 1


@parameters
def test_check_reports_green_only_when_apply_is_a_noop(tmp_path, ext, newline, bom):
    """--check must not pass a file that an apply run would still rewrite"""
    source = write_source(tmp_path / f"sample.{ext}", ext, newline, bom)

    assert run(source, "--check") == 1

    run(source)
    processed = source.read_bytes()

    assert run(source, "--check") == 0
    assert source.read_bytes() == processed


@pytest.mark.parametrize("newline", ["\r\n", "\n"])
@pytest.mark.parametrize("ext", list(sources))
def test_existing_header_is_detected_behind_a_bom(tmp_path, ext, newline):
    """A BOM must not hide an existing header from detection

    Decoding the mark as a character left it in front of the comment marker, so
    the header was not recognised and a second one was rendered above it.
    """
    # A file that already carries a correct header
    reference = write_source(tmp_path / f"reference.{ext}", ext, newline, False)
    run(reference)

    # The same content, written with a BOM as Visual Studio would
    source = tmp_path / f"sample.{ext}"
    source.write_bytes(codecs.BOM_UTF8 + reference.read_bytes())

    assert run(source) == 0

    data = source.read_bytes()
    assert data.count(copyright_marker) == 1
    assert data == codecs.BOM_UTF8 + reference.read_bytes()


def test_mixed_line_endings_are_left_as_they_are(tmp_path):
    """Only the rendered header is ours to decide the line ending for"""
    source = tmp_path / "sample.cs"
    source.write_bytes(b"using System;\r\n\r\nnamespace Demo\n{\n}\n")

    assert run(source) == 0

    data = source.read_bytes()
    header, body = data.split(b"using System;", 1)

    # The header follows the first line ending below the prologue, the file
    # has none, so the first line ending of the file
    assert line_endings(header) == {b"\r\n"}
    # The body keeps the endings it already had
    assert body == b"\r\n\r\nnamespace Demo\n{\n}\n"


def test_header_follows_the_line_ending_below_the_prologue(tmp_path):
    """A shebang with another line ending does not decide for the header"""
    source = tmp_path / "sample.ts"
    source.write_bytes(b"#!/usr/bin/env node\nfoo();\r\n")

    assert run(source) == 0

    data = source.read_bytes()
    assert data.startswith(b"#!/usr/bin/env node\n/*!")
    header = data[len(b"#!/usr/bin/env node\n") : data.index(b"foo();")]
    assert line_endings(header) == {b"\r\n"}


def test_up_to_date_header_below_a_prologue_is_left_alone(tmp_path):
    source = tmp_path / "sample.ts"
    source.write_bytes(b"#!/usr/bin/env node\nfoo();\n")
    run(source)
    # The shebang line of the processed file now ends with CRLF
    processed = source.read_bytes().replace(b"node\n", b"node\r\n", 1)
    source.write_bytes(processed)

    assert run(source, "--check") == 0
    assert run(source) == 0
    assert source.read_bytes() == processed


def test_byte_order_mark_stays_in_front_of_a_doctype(tmp_path):
    source = write_source(tmp_path / "sample.html", "html", "\n", True)

    assert run(source) == 0

    assert source.read_bytes().startswith(codecs.BOM_UTF8 + b"<!DOCTYPE html>\n<!--\n")


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
@pytest.mark.parametrize(
    "path", OUTPUTS, ids=[os.path.relpath(p, test_dir) for p in OUTPUTS]
)
def test_scenario_with_other_line_endings(tmp_path, path, newline):
    """Every scenario gives the same result with other line endings"""
    relative = os.path.relpath(path, test_dir + "/output")
    directory = relative.split(os.sep)[0]
    name = scenario(path)
    config = f"{test_dir}/config/{directory}/{CONFIGS.get(name, name)}.yml"

    def convert(file):
        with open(file, "rb") as src:
            return src.read().replace(b"\n", newline.encode("utf-8"))

    source = tmp_path / os.path.basename(path)
    source.write_bytes(convert(test_dir + "/input/" + relative))

    main(["-c", config, "--file", str(source)])

    assert source.read_bytes() == convert(path)

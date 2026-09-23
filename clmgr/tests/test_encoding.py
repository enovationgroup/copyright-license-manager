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

test_dir = os.path.dirname(os.path.realpath(__file__))

config_file = test_dir + "/config/default/single.yml"

# A source file per comment style: block comments (cs, sql) and line comments (py)
sources = {
    "cs": ["using System;", "", "namespace Demo", "{", "}"],
    "py": ["import os", "", "print(os.name)"],
    "sql": ["select 1;"],
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


def line_endings(path):
    """The distinct line endings used in a file"""
    return set(re.findall(rb"\r\n|\r|\n", path.read_bytes()))


def run(path, *extra_args):
    """Run clmgr on a single file and return its exit code"""
    return main(["-c", config_file, "--file", str(path)] + list(extra_args))


def assert_encoding_preserved(path, newline, bom):
    """The file carries exactly one BOM, at the front, and one line ending"""
    data = path.read_bytes()

    assert data.startswith(codecs.BOM_UTF8) is bom
    assert data.count(codecs.BOM_UTF8) == (1 if bom else 0)
    assert line_endings(path) == {newline.encode("utf-8")}


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

    A BOM used to hide the existing header from detection, so the run appended
    a second one below the first.
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


@pytest.mark.parametrize("ext", list(sources))
def test_existing_header_is_detected_behind_a_bom(tmp_path, ext):
    """A BOM must not hide an existing header from detection

    Decoding the mark as a character left it in front of the comment marker, so
    the header was not recognised and a second one was rendered above it.
    """
    # A file that already carries a correct header
    reference = write_source(tmp_path / f"reference.{ext}", ext, "\n", False)
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

    # The header follows the first line ending in the file
    assert line_endings_of(header) == {b"\r\n"}
    # The body keeps the endings it already had
    assert body == b"\r\n\r\nnamespace Demo\n{\n}\n"


def line_endings_of(data):
    return set(re.findall(rb"\r\n|\r|\n", data))

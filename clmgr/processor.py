"""Processor functions"""

import codecs
import datetime
import os
import re
import shutil
import tempfile

from clmgr.template import template, comments


def _detect_newline(lines, default="\n"):
    """Determine the line ending used by a source file.

    The first line ending in the file decides, because the header we render is
    placed at the top. Files without any line ending fall back to `default`
    rather than to the platform separator: the tool commonly runs on Linux CI
    over repositories written on Windows, so `os.linesep` would be the wrong
    guess there.

    Parameters
    ----------
    lines
        File contents, as read by `read_file`
    default
        Line ending to assume for a file that contains none

    Returns
    -------
        One of "\r\n", "\n" or "\r"

    """
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
        if line.endswith("\r"):
            return "\r"

    return default


def _has_bom(path):
    """Report whether a file starts with a UTF-8 byte order mark"""
    with open(file=path, mode="rb") as src:
        return src.read(len(codecs.BOM_UTF8)) == codecs.BOM_UTF8


def read_file(path):
    """Read a source file without altering how it is encoded.

    A byte order mark is consumed rather than decoded, so it cannot end up in
    the middle of the file once a header is rendered above the first line, and
    so header detection is not thrown off by a `\ufeff` in front of the comment
    marker. Line endings are read verbatim instead of being normalised to "\n",
    which keeps every line the tool does not touch byte for byte identical.

    Both properties are restored by `write_file`.

    Parameters
    ----------
    path
        Path of the source file

    Returns
    -------
        The file contents as a list of lines

    """
    with open(file=path, encoding="utf-8-sig", mode="r", newline="") as src:
        return src.readlines()


def _find_first_non_empty_line_index(lines):
    for idx, line in enumerate(lines):
        if line.strip() != "":
            return idx
    return None


def _infer_line_prefix_from_header_body(header_body_lines, char, fallback_line_prefix):
    """Infer the line prefix for comment body lines from an existing header.

    This keeps formatting stable across languages and user styles.
    Example:
    - Java/C#: ' * '
    - SQL fixtures here: '  '
    """

    for raw in header_body_lines:
        if raw.strip() == "":
            continue

        m = re.match(r"^(\s*)(.*)$", raw)
        if not m:
            break

        leading_ws = m.group(1)
        rest = m.group(2)

        # If the line uses a leading comment char (e.g. '*'), keep it.
        stripped = rest.lstrip()
        if char and stripped.startswith(char):
            # Preserve a single space after the char when present/desired.
            after_char = stripped[len(char) :]
            if after_char.startswith(" "):
                return f"{leading_ws}{char} "
            return f"{leading_ws}{char}"

        # Otherwise it's likely indentation-only style.
        return leading_ws

    return fallback_line_prefix


def _find_header_block(lines, start, end, max_region=None, max_header_lines=500):
    """Find the first top-of-file header block.

    Returns a tuple: (start_idx, end_idx, body_lines, end_line)
    - start_idx/end_idx are indices in `lines` (inclusive)
    - body_lines excludes start/end delimiters
    - end_line is the original end delimiter line (including newline) when present

    This is intentionally position-agnostic:
    - it ignores leading whitespace when matching `start`
    - for block comments it matches `end` by containment (`end in line`)
    - supports single-line comment styles where start==end (e.g. '#')
    """

    if not lines:
        return None

    start_search_upto = len(lines)
    if max_region is not None:
        start_search_upto = min(start_search_upto, max_region)

    first_idx = _find_first_non_empty_line_index(lines[:start_search_upto])
    if first_idx is None:
        return None

    first_line = lines[first_idx]
    if not first_line.lstrip().startswith(start):
        return None

    # Single-line comment style (py/sh): header is a run of comment lines.
    if start == end:
        end_idx = first_idx
        for idx in range(first_idx, start_search_upto):
            if lines[idx].lstrip().startswith(start):
                end_idx = idx
            else:
                break
        body = lines[first_idx : end_idx + 1]
        return first_idx, end_idx, body, None

    # Block comment style (java/cs/sql/ts): find the terminating marker.
    # Handle `/* ... */` on a single line.
    if end in first_line and first_line.lstrip().startswith(start):
        # Preserve any content after the start token and before end token as body.
        after_start = first_line.split(start, 1)[1]
        before_end = after_start.split(end, 1)[0]
        body = []
        if before_end.strip() != "":
            body.append(
                before_end + "\n" if not before_end.endswith("\n") else before_end
            )
        return first_idx, first_idx, body, first_line

    scan_upto = min(len(lines), first_idx + max_header_lines)
    for idx in range(first_idx + 1, scan_upto):
        if end in lines[idx]:
            body = lines[first_idx + 1 : idx]
            return first_idx, idx, body, lines[idx]

    return None


def render_insert(cfg, ext, offset, lines):
    """Render the file contents with a new copyright header inserted.

    Parameters
    ----------
    cfg
        Parsed configuration
    ext
        Source file extension, used to look up the comment style
    offset
        Number of leading lines that must be preserved as-is (e.g. shebang)
    lines
        Original file contents

    Returns
    -------
        The new file contents as a list of lines. The input is left untouched.

    """
    nl = _detect_newline(lines)
    out = lines[:offset]
    lines = lines[offset:]

    start = comments.get(ext).get("start")
    char = comments.get(ext).get("char")
    line = comments.get(ext).get("line")
    end = comments.get(ext).get("end")
    divider = comments.get(ext).get("divider")
    license_start = comments.get(ext).get("license").get("start")
    license_end = comments.get(ext).get("license").get("end")

    # Detect an existing header block at the top of the file (position-agnostic)
    header = _find_header_block(lines, start, end)
    header_detected = header is not None
    header_body_lines = []
    header_end_line = None
    if header_detected:
        header_start_idx, header_end_idx, header_body_lines, header_end_line = header
        # Remove the entire original header (we'll re-create it)
        del lines[header_start_idx : header_end_idx + 1]

        # For single-line comment styles (e.g. '#'), we already write a leading
        # start marker line ourselves, so drop an existing bare start marker
        # to avoid duplication. Also drop trailing bare marker since we write
        # end + nl ourselves.
        if start == end and header_body_lines:
            first = header_body_lines[0]
            if first.strip() == start:
                header_body_lines = header_body_lines[1:]
            if header_body_lines:
                last = header_body_lines[-1]
                if last.strip() == end:
                    header_body_lines = header_body_lines[:-1]

    line_prefix = line
    if header_detected and start != end:
        line_prefix = _infer_line_prefix_from_header_body(header_body_lines, char, line)

    out.append(start + nl)
    legal_entities = cfg["legal"]
    legal_entities_idx = 0
    for legal in legal_entities:
        year = datetime.datetime.now().year

        if legal_entities_idx < len(legal_entities) - 1:
            year = legal_entities[legal_entities_idx + 1]["inception"]

        tmpl = template(
            cfg["format"],
            legal["inception"],
            year,
            legal["name"],
            legal["locality"],
            legal["country"],
        )
        out.append(line_prefix + tmpl + nl)
        legal_entities_idx += 1

    if divider:
        out.append(line_prefix.rstrip() + nl)
    if cfg["license"]["enabled"]:
        if license_start != "":
            out.append(line_prefix + license_start + nl)
        if cfg["license"]["external"] is False:
            out.append(line_prefix + cfg["license"]["content"] + nl)
        # TODO: Read license file
        if license_end != "":
            out.append(line_prefix + license_end + nl)
        if divider:
            out.append(line_prefix.rstrip() + nl)

    if header_detected:
        # Write user header body as-is, then close the comment.
        out.extend(header_body_lines)
        if header_end_line is not None:
            if header_end_line.endswith(("\n", "\r")):
                out.append(header_end_line)
            else:
                out.append(header_end_line + nl)
        else:
            out.append(end + nl)
    else:
        out.append(end + nl)

    # Append remaining lines
    out.extend(lines)

    return out


def render_update(cfg, ext, offset, lines, args):
    """Render the file contents with the existing copyright header updated.

    Parameters
    ----------
    cfg
        Parsed configuration
    ext
        Source file extension, used to look up the comment style
    offset
        Number of leading lines that must be preserved as-is (e.g. shebang)
    lines
        Original file contents
    args
        Parsed commandline arguments

    Returns
    -------
        The new file contents as a list of lines. The input is left untouched.

    """
    nl = _detect_newline(lines)
    out = lines[:offset]
    lines = lines[offset:]

    start = comments.get(ext).get("start")
    char = comments.get(ext).get("char")
    line = comments.get(ext).get("line")
    divider = comments.get(ext).get("divider")
    end = comments.get(ext).get("end")

    # Detect header block (position-agnostic) within the configured region.
    header = _find_header_block(lines, start, end, max_region=args.region)
    header_start_idx = None
    header_end_idx = None
    header_body_lines = []
    if header is not None:
        header_start_idx, header_end_idx, header_body_lines, _ = header

    line_prefix = line
    if header_start_idx is not None and start != end:
        line_prefix = _infer_line_prefix_from_header_body(header_body_lines, char, line)

    # Get Copyright block
    # This block contains only the copyright lines
    # Remove existing copyright lines inside the header area, regardless of indentation.
    if header_start_idx is not None and header_end_idx is not None:
        header_slice_end = min(header_end_idx + 1, len(lines))
        for idx in range(header_slice_end - 1, header_start_idx - 1, -1):
            if "Copyright" in lines[idx]:
                lines.pop(idx)

    legal_entities = cfg["legal"]
    idx = 0
    # Insert copyright lines right after the header start (or at top if no header).
    insert_at = 0
    if header_start_idx is not None:
        insert_at = header_start_idx + 1

    for lid in range(len(legal_entities)):
        legal = legal_entities[lid]
        year = datetime.datetime.now().year

        if lid < len(legal_entities) - 1:
            year = legal_entities[lid + 1]["inception"]

        tmpl = template(
            cfg["format"],
            legal["inception"],
            year,
            legal["name"],
            legal["locality"],
            legal["country"],
        )
        lines.insert(insert_at + lid, line_prefix + tmpl + nl)
        idx = insert_at + lid

    # Detect license block
    if cfg["license"]["enabled"]:
        license_start = comments.get(ext).get("license").get("start")
        license_end = comments.get(ext).get("license").get("end")
        license_detected = False
        license_start_idx = 0
        license_end_idx = 0
        license_block = []  # noqa: F841
        # Search for the start of the License with the search region
        # If found record index
        # Search again for end region, this can be larger than the initial
        # search region therefor to not include the search region when searching
        # for the license termination marker
        for x in range(len(lines)):
            if license_start in lines[x] and x <= args.region:
                license_detected = True  # We found a license block
                license_start_idx = x  # Record the start index

        for x in range(len(lines)):
            if license_end in lines[x] and x > license_start_idx:
                license_end_idx = x

        if license_detected:
            # TODO: Process license further if required
            license_block = lines[license_start_idx:license_end_idx]  # noqa: F841
        else:
            insert_idx = idx + 1
            if divider:
                lines.insert(insert_idx, line_prefix.rstrip() + nl)
                insert_idx += 1
            lines.insert(insert_idx, line_prefix + license_start + nl)
            if cfg["license"]["external"] is False:
                lines.insert(
                    insert_idx + 1, line_prefix + cfg["license"]["content"] + nl
                )
            # TODO: Read license file
            lines.insert(insert_idx + 2, line_prefix + license_end + nl)

    # Append all remaining lines
    out.extend(lines)

    return out


def analyze(cfg, ext, lines, args):
    """Determine what clmgr would do with a source file, without touching it.

    Parameters
    ----------
    cfg
        Parsed configuration
    ext
        Source file extension, used to look up the comment style
    lines
        Original file contents
    args
        Parsed commandline arguments

    Returns
    -------
        A tuple (action, new_lines) where action is one of "add", "update" or
        "none". For "none" the returned contents are the original contents.

    """
    offset = 0

    try:
        # Shell
        # TODO: Implementation
        if ext.lower() == "sh":
            offset = 1

        # Determine insert vs update by scanning the header block rather than
        # relying on a fixed line index (SQL and indented headers break that).
        start = comments.get(ext).get("start")
        end = comments.get(ext).get("end")
        scan_lines = lines[offset:]
        header = _find_header_block(scan_lines, start, end, max_region=args.region)
        header_has_copyright = False
        if header is not None:
            _, _, header_body_lines, _ = header
            header_has_copyright = any(
                "Copyright" in line for line in header_body_lines
            )

        if not header_has_copyright:
            return "add", render_insert(cfg, ext, offset, lines)

        new_lines = render_update(cfg, ext, offset, lines, args)
        if new_lines != lines:
            return "update", new_lines
    except IndexError:
        pass

    return "none", lines


def write_file(path, lines):
    """Replace the contents of a source file with the rendered contents.

    The new contents are written to a temporary file in the same directory and
    moved into place, so an interrupted run cannot leave a partially written
    source file behind.

    A file that was read with a byte order mark is written back with one, and
    the lines keep the endings they were read with, so the only difference from
    the original is the header itself.

    Parameters
    ----------
    path
        Path of the source file
    lines
        The new file contents

    Returns
    -------
        None

    """
    target = path.absolute()
    # The mark was consumed while reading, so whether to write one back is
    # answered by the file we are about to replace.
    encoding = "utf-8-sig" if _has_bom(target) else "utf-8"
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=target.name, suffix=".tmp")
    try:
        with os.fdopen(fd, encoding=encoding, mode="w", newline="") as dst:
            dst.writelines(lines)
        shutil.copymode(target, tmp)
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

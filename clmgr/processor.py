"""Processor functions"""

import datetime
import logging
import os
import re
import shutil
import tempfile

from clmgr.template import template, comments

log = logging.getLogger("root")

BOM = "\ufeff"


def _find_first_non_empty_line_index(lines):
    for idx, line in enumerate(lines):
        if line.strip() != "":
            return idx
    return None


def count_prologue_lines(lines, prologue):
    """Count the leading lines that must stay above the copyright header.

    Some files have to start with a specific construct, such as a shebang,
    a CSS `@charset` rule or an HTML doctype. Those lines are left in place
    and the header is placed below them.

    Parameters
    ----------
    lines
        Original file contents
    prologue
        Compiled patterns of the constructs that must stay on top, each one
        consuming whole lines. They are matched in order, at most once each.

    Returns
    -------
        The number of leading lines that belong to the prologue

    """
    if not prologue:
        return 0

    text = "".join(lines)
    pos = 0
    for pattern in prologue:
        match = pattern.match(text, pos)
        if match:
            pos = match.end()

    consumed = text[:pos]
    count = consumed.count("\n")
    if consumed and not consumed.endswith("\n"):
        count += 1

    return count


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


def _find_header_block(
    lines, start, end, max_region=None, max_header_lines=500, indented=False
):
    """Find the first top-of-file header block.

    Returns a tuple: (start_idx, end_idx, body_lines, end_line)
    - start_idx/end_idx are indices in `lines` (inclusive)
    - body_lines excludes start/end delimiters
    - end_line is the original end delimiter line (including newline) when present

    This is intentionally position-agnostic:
    - it ignores leading whitespace when matching `start`
    - for block comments it matches `end` by containment (`end in line`)
    - supports single-line comment styles where start==end (e.g. '#')
    - with `indented`, a block comment also ends before the first line that
      is not indented, as in the indented syntax of Sass
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
        if indented and lines[idx].strip() != "" and not lines[idx][0].isspace():
            body = lines[first_idx + 1 : idx]
            return first_idx, idx - 1, body, None

    return None


def _has_copyright(header_body_lines):
    return any("Copyright" in line for line in header_body_lines)


def detect_header(lines, ext, max_region=None):
    """Find the existing header of a file and the comment style it uses.

    A header in the comment style of new headers is always recognised. A
    header in one of the legacy styles of the extension is only recognised
    when it holds a copyright statement.

    Parameters
    ----------
    lines
        File contents, without the prologue
    ext
        Source file extension, used to look up the comment styles
    max_region
        Number of lines the header must start in

    Returns
    -------
        A tuple (header_style, header), both None when there is no header.
        The header is the tuple returned by `_find_header_block`.

    """
    comment = comments.get(ext)
    candidates = [(comment, False)]
    candidates += [(legacy, True) for legacy in comment["legacy"]]

    for header_style, copyright_only in candidates:
        header = _find_header_block(
            lines,
            header_style["start"],
            header_style["end"],
            max_region=max_region,
            indented=header_style.get("indented", False),
        )
        if header is None:
            continue
        # The copyright may still be on the first line of the comment
        if copyright_only and not _has_copyright(lines[header[0] : header[1] + 1]):
            continue
        return header_style, header

    return None, None


def _split_header_start(line, header_style, single_line):
    """Move the text on the first line of a block comment to a line of its own.

    `<!-- text -->` becomes the start marker, the text and the end marker on
    lines of their own, and `/* text` becomes the start marker followed by the
    text. A header can then be written into it like into any other block
    comment. Code following a single line comment is kept on its own line.

    Parameters
    ----------
    line
        The first line of the comment
    header_style
        The comment style the comment is written in
    single_line
        Whether the comment ends on the same line

    Returns
    -------
        The lines replacing the first line of the comment

    """
    start = header_style["start"]
    end = header_style["end"].strip()

    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    rest = stripped[len(start) :]
    # Keep the marker of /*! and /** comments, and the rule of a banner
    marker = re.match(r"[!* \t]*", rest).group(0).rstrip()
    rest = rest[len(marker) :]

    after = ""
    if single_line:
        rest, _, after = rest.partition(end)
    elif rest.strip() == "":
        return [line]

    lines = [indent + start + marker + "\n"]
    if rest.strip() != "":
        lines.append(indent + header_style["line"] + rest.strip() + "\n")
    if single_line:
        lines.append(indent + header_style["end"] + "\n")
        if after.strip() != "":
            lines.append(after.strip() + "\n")

    return lines


def _is_marker(line, marker, char):
    """Whether a header line consists of nothing but a license marker"""
    text = line.strip()
    if char and text.startswith(char):
        text = text[len(char) :].strip()
    return text == marker


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
    out = lines[:offset]
    lines = lines[offset:]

    # A prologue on the last line of a file has no line ending to separate it
    # from the header that follows
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"

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
        # end + "\n" ourselves.
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

    out.append(start + "\n")
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
        out.append(line_prefix + tmpl + "\n")
        legal_entities_idx += 1

    if divider:
        out.append(line_prefix.rstrip() + "\n")
    if cfg["license"]["enabled"]:
        if license_start != "":
            out.append(line_prefix + license_start + "\n")
        if cfg["license"]["external"] is False:
            out.append(line_prefix + cfg["license"]["content"] + "\n")
        # TODO: Read license file
        if license_end != "":
            out.append(line_prefix + license_end + "\n")
        if divider:
            out.append(line_prefix.rstrip() + "\n")

    if header_detected:
        # Write user header body as-is, then close the comment.
        out.extend(header_body_lines)
        if header_end_line is not None:
            if header_end_line.endswith("\n"):
                out.append(header_end_line)
            else:
                out.append(header_end_line + "\n")
        else:
            out.append(end + "\n")
    else:
        out.append(end + "\n")

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
    out = lines[:offset]
    lines = lines[offset:]

    divider = comments.get(ext).get("divider")

    # Detect header block (position-agnostic) within the configured region.
    # The header is updated in the comment style it is written in.
    header_style, header = detect_header(lines, ext, max_region=args.region)
    if header_style is None:
        header_style = comments.get(ext)
    start = header_style["start"]
    char = header_style["char"]
    line = header_style["line"]
    end = header_style["end"]

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
    removed = 0
    if header_start_idx is not None and header_end_idx is not None:
        header_slice_end = min(header_end_idx + 1, len(lines))
        for idx in range(header_slice_end - 1, header_start_idx - 1, -1):
            if "Copyright" in lines[idx]:
                lines.pop(idx)
                removed += 1

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
        lines.insert(insert_at + lid, line_prefix + tmpl + "\n")
        idx = insert_at + lid

    # Detect license block
    if cfg["license"]["enabled"]:
        license_start = comments.get(ext).get("license").get("start")
        license_end = comments.get(ext).get("license").get("end")

        # Only a line that holds nothing but the marker starts the license,
        # so separator lines such as ===== in the header are not mistaken
        # for it
        license_detected = False
        if header_start_idx is not None:
            header_end = header_end_idx - removed + len(legal_entities)
            license_detected = any(
                _is_marker(lines[x], license_start, char)
                for x in range(header_start_idx, min(header_end + 1, len(lines)))
            )

        if not license_detected:
            insert_idx = idx + 1
            if divider:
                lines.insert(insert_idx, line_prefix.rstrip() + "\n")
                insert_idx += 1
            lines.insert(insert_idx, line_prefix + license_start + "\n")
            if cfg["license"]["external"] is False:
                lines.insert(
                    insert_idx + 1, line_prefix + cfg["license"]["content"] + "\n"
                )
            # TODO: Read license file
            lines.insert(insert_idx + 2, line_prefix + license_end + "\n")

    # Append all remaining lines
    out.extend(lines)

    return out


def analyze(cfg, ext, lines, path, args):
    """Determine what clmgr would do with a source file, without touching it.

    Parameters
    ----------
    cfg
        Parsed configuration
    ext
        Source file extension, used to look up the comment style
    lines
        Original file contents
    path
        Path of the source file, used for reporting
    args
        Parsed commandline arguments

    Returns
    -------
        A tuple (action, new_lines) where action is one of "add", "update" or
        "none". For "none" the returned contents are the original contents.

    """
    original = lines

    try:
        # A byte order mark belongs in front of the whole file, it is set
        # aside while the header is rendered
        bom = ""
        if lines and lines[0].startswith(BOM):
            bom = BOM
            lines = [lines[0][len(BOM) :]] + lines[1:]

        # Lines such as a shebang or doctype must stay at the top of the file
        offset = count_prologue_lines(lines, comments.get(ext)["prologue"])

        # Determine insert vs update by scanning the header block rather than
        # relying on a fixed line index (SQL and indented headers break that).
        scan_lines = lines[offset:]
        header_style, header = detect_header(scan_lines, ext, max_region=args.region)

        # Text on the first line of a block comment is moved to a line of its
        # own, so the header can be handled like every other header
        if header is not None and header_style["start"] != header_style["end"]:
            header_start_idx, header_end_idx, _, _ = header
            idx = offset + header_start_idx
            split = _split_header_start(
                lines[idx], header_style, header_start_idx == header_end_idx
            )
            if split != [lines[idx]]:
                lines = lines[:idx] + split + lines[idx + 1 :]
                scan_lines = lines[offset:]
                header_style, header = detect_header(
                    scan_lines, ext, max_region=args.region
                )

        if header is None or not _has_copyright(header[2]):
            action = "add"
            new_lines = render_insert(cfg, ext, offset, lines)
        else:
            action = "update"
            new_lines = render_update(cfg, ext, offset, lines, args)

        if bom:
            new_lines = [bom + new_lines[0]] + new_lines[1:]

        if new_lines != original:
            return action, new_lines
    except IndexError:
        log.warning(f"Skipping {path}, could not locate a header to work with")

    return "none", original


def write_file(path, lines):
    """Replace the contents of a source file with the rendered contents.

    The new contents are written to a temporary file in the same directory and
    moved into place, so an interrupted run cannot leave a partially written
    source file behind.

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
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=target.name, suffix=".tmp")
    try:
        with os.fdopen(fd, encoding="utf-8", mode="w") as dst:
            dst.writelines(lines)
        shutil.copymode(target, tmp)
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

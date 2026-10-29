"""Processor functions"""

import codecs
import datetime
import logging
import os
import re
import shutil
import tempfile

from clmgr.template import comments, statements

log = logging.getLogger("root")


def _detect_newline(lines, default="\n"):
    r"""Determine the line ending used by a source file.

    The first line ending in the lines decides. `analyze` passes the lines
    from where the header is or goes, so a prologue with a different line
    ending, such as a shebang, does not decide for the header. Files without
    any line ending fall back to `default`
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
    r"""Read a source file without altering how it is encoded.

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
    count = len(re.findall(r"\r\n|\r|\n", consumed))
    if consumed and not consumed.endswith(("\n", "\r")):
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
        # An empty line, or one holding only the comment char (" *"), does not
        # show the whitespace that follows the char on a line with text
        if raw.strip() == "" or (char and raw.strip() == char):
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
    """Find the first comment of a file, the candidate for its header.

    Returns a tuple: (start_idx, end_idx, body_lines, end_line)
    - start_idx/end_idx are indices in `lines` (inclusive)
    - body_lines excludes start/end delimiters
    - end_line is the original end delimiter line (including newline) when present

    This is intentionally position-agnostic:
    - it ignores leading whitespace when matching `start`
    - for block comments it matches `end` by containment (`end in line`),
      without the whitespace a style writes in front of the end marker
    - supports single-line comment styles where start==end (e.g. '#')
    - with `indented`, a block comment also ends before the first line that
      is not indented or with the file, as in the indented syntax of Sass
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

    # Line comment style (py/sass): header is a run of comment lines. The
    # region limits where the header starts, not how long it is.
    if start == end:
        end_idx = first_idx
        for idx in range(first_idx, min(len(lines), first_idx + max_header_lines)):
            if lines[idx].lstrip().startswith(start):
                end_idx = idx
            else:
                break
        body = lines[first_idx : end_idx + 1]
        return first_idx, end_idx, body, None

    # Block comment style: find the terminating marker. Only the marker
    # itself counts, so a header closed by */ at the start of a line ends
    # there and does not run on to a later line holding " */".
    end = end.strip()

    # Handle `/* ... */` on a single line.
    after_start = first_line.split(start, 1)[1]
    if end in after_start:
        # Preserve any content after the start token and before end token as body.
        before_end = after_start.split(end, 1)[0]
        body = []
        if before_end.strip() != "":
            body.append(before_end + _detect_newline([first_line]))
        return first_idx, first_idx, body, first_line

    scan_upto = min(len(lines), first_idx + max_header_lines)
    for idx in range(first_idx + 1, scan_upto):
        if end in lines[idx]:
            body = lines[first_idx + 1 : idx]
            return first_idx, idx, body, lines[idx]
        if indented and lines[idx].strip() != "" and not lines[idx][0].isspace():
            body = lines[first_idx + 1 : idx]
            return first_idx, idx - 1, body, None

    # An indented comment that is not followed by a line that is not
    # indented ends with the file
    if indented and scan_upto == len(lines):
        return first_idx, len(lines) - 1, lines[first_idx + 1 :], None

    return None


def _has_copyright(header_body_lines):
    return any("Copyright" in line for line in header_body_lines)


def _comment_lines(lines, block, comment_style):
    """The lines of a comment found by `_find_header_block`.

    Returns a tuple (comment_lines, after): the lines of the comment, the
    last one up to and including its end marker, and the text that follows
    the end marker on that line, such as code or another comment.
    """
    start_idx, end_idx, _, end_line = block
    comment_lines = lines[start_idx : end_idx + 1]

    # Line comments, and an indented Sass comment, end with their last line
    if end_line is None:
        return comment_lines, ""

    last = comment_lines[-1]
    if start_idx == end_idx:
        # The end marker is searched for after the start marker, as in /**/
        stripped = last.lstrip()
        marker_at = len(last) - len(stripped) + len(comment_style["start"])
    else:
        marker_at = 0
    end = comment_style["end"].strip()
    after = last[marker_at:].partition(end)[2]

    return comment_lines[:-1] + [last[: len(last) - len(after)]], after


def _comment_has_copyright(lines, header, header_style):
    """Whether a comment found by `_find_header_block` holds a copyright.

    The first line of the comment counts as well, text that follows the
    comment on its last line, such as a second comment, does not.
    """
    return _has_copyright(_comment_lines(lines, header, header_style)[0])


def _candidate_styles(ext):
    """The comment styles a header of an extension may be written in.

    Returns a list of (header_style, copyright_only) tuples: the style of new
    headers first, then the legacy styles, which only count as the header
    when the comment holds a copyright statement. A comment in the style of
    new headers also only counts when it holds one if the style is marked
    `copyright_only`, as markup and Sass are.
    """
    comment = comments.get(ext)
    candidates = [(comment, comment["copyright_only"])]
    return candidates + [(legacy, True) for legacy in comment["legacy"]]


def _find_comment(lines, header_style, max_region):
    """Find the first comment of a file in one comment style"""
    return _find_header_block(
        lines,
        header_style["start"],
        header_style["end"],
        max_region=max_region,
        indented=header_style.get("indented", False),
    )


def detect_header(lines, ext, max_region=None):
    """Find the existing header of a file and the comment style it uses.

    A header in the comment style of new headers is recognised, unless the
    style is marked `copyright_only` and the comment holds no copyright
    statement. A header in one of the
    legacy styles of the extension is only recognised when it holds one.

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
    for header_style, copyright_only in _candidate_styles(ext):
        header = _find_comment(lines, header_style, max_region)
        if header is None:
            continue
        if copyright_only and not _comment_has_copyright(lines, header, header_style):
            continue
        return header_style, header

    return None, None


def _closing(header_style):
    """The end marker clmgr writes when it moves text off a comment line"""
    return header_style.get("close", header_style["end"])


def _is_decoration(text):
    """Whether comment text is decoration, such as a rule of stars or dashes"""
    return re.search(r"[^\W_]", text) is None


def _split_header_start(line, header_style, single_line, nl):
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
    nl
        Line ending of the lines that are written

    Returns
    -------
        The lines replacing the first line of the comment

    """
    start = header_style["start"]
    end = header_style["end"].strip()

    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    rest = stripped[len(start) :]
    # Keep the marker of /*! and /** comments, it directly follows the start.
    # The star of an end marker, as in /**/, is not part of it.
    marker = re.match(r"(?:!|\*(?!/))*", rest).group(0)
    rest = rest[len(marker) :]

    after = ""
    if single_line:
        rest, _, after = rest.partition(end)

    # Decoration, such as the rule of stars of a banner or /*-----, is not
    # text that has to be moved
    text = rest.strip()
    if _is_decoration(text):
        text = ""
        if not single_line:
            return [line]

    lines = [indent + start + marker + nl]
    if text != "":
        lines.append(indent + header_style["line"] + text + nl)
    if single_line:
        lines.append(indent + _closing(header_style) + nl)
        if after.strip() != "":
            lines.append(after.strip() + nl)

    return lines


def _split_header_end(line, header_style, nl):
    """Move the text on the last line of a block comment to a line of its own.

    `text */` becomes the text followed by the end marker, and code following
    the end marker is kept on a line of its own below it.

    Parameters
    ----------
    line
        The last line of the comment
    header_style
        The comment style the comment is written in
    nl
        Line ending of the lines that are written

    Returns
    -------
        The lines replacing the last line of the comment

    """
    before, end, after = line.partition(header_style["end"].strip())
    if after.strip() == "" and _is_decoration(before):
        return [line]

    lines = []
    if before.strip() == "":
        lines.append(_closing(header_style) + nl)
    elif _is_decoration(before):
        # Decoration, such as " **/" or "-----*/", stays with the end marker
        lines.append(before.rstrip() + end + nl)
    else:
        lines.append(before.rstrip() + nl)
        lines.append(_closing(header_style) + nl)
    if after.strip() != "":
        lines.append(after.strip() + nl)

    return lines


def _copyrights_outside_header(lines, ext, header_style, header, max_region):
    """The copyright statements in comments other than the header.

    Every comment that starts within the region, at the start of a line or
    directly after another comment, is checked, in the comment styles a
    header may be written in and in the other comment styles of the
    extension. Code that follows a comment on its last line is not checked.

    Parameters
    ----------
    lines
        File contents, without the prologue
    ext
        Source file extension, used to look up the comment styles
    header_style
        The comment style the header is written in, or None
    header
        The header as returned by `_find_header_block`, or None
    max_region
        Number of lines a comment must start in

    Returns
    -------
        The lines of the comments holding a copyright statement, stripped

    """
    comment = comments.get(ext)
    styles = [candidate for candidate, _ in _candidate_styles(ext)]
    styles += comment["other_comments"]

    found = []
    idx = 0
    # The text of line idx that is still to be checked
    text = None
    while idx < min(len(lines), max_region):
        if text is None and header is not None and idx == header[0]:
            # The header is the first comment, nothing precedes it on its line
            text = _comment_lines(lines, header, header_style)[1]
            idx = header[1]
        elif text is None:
            text = lines[idx]

        remaining = [text] + lines[idx + 1 :]
        block = None
        for block_style in styles:
            if text.lstrip().startswith(block_style["start"]):
                block = _find_comment(remaining, block_style, None)
                if block is not None:
                    break

        if block is None:
            text = None
            idx += 1
            continue

        comment_lines, after = _comment_lines(remaining, block, block_style)
        found += [line.strip() for line in comment_lines if _has_copyright([line])]

        # Another comment may follow on the line the comment ends on
        idx += block[1]
        text = after if after.strip() != "" else None
        if text is None:
            idx += 1

    return found


def current_year():
    """The year the copyright of the last legal entity ends in"""
    return datetime.datetime.now().year


def _statements(cfg):
    """The copyright statements of the configuration, up to the current year"""
    return statements(cfg["format"], cfg["legal"], current_year())


def _license_content(cfg, line_prefix, nl):
    """The license content as header lines.

    The content may span several lines. Every line gets the line prefix, so
    it stays inside a header of line comments, and an empty line gets the
    prefix without its trailing whitespace.
    """
    return [
        line_prefix + text + nl if text.strip() != "" else line_prefix.rstrip() + nl
        for text in cfg["license"]["content"].splitlines()
    ]


def _is_marker(line, marker, char):
    """Whether a header line consists of nothing but a license marker"""
    text = line.strip()
    if char and text.startswith(char):
        text = text[len(char) :].strip()
    return text == marker


def render_insert(cfg, ext, offset, lines, nl, max_region=None):
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
    nl
        Line ending of the lines that are written
    max_region
        Number of lines an existing header must start in, as in `analyze`

    Returns
    -------
        The new file contents as a list of lines. The input is left untouched.

    """
    out = lines[:offset]
    lines = lines[offset:]

    # A prologue on the last line of a file has no line ending to separate it
    # from the header that follows
    if out and not out[-1].endswith(("\n", "\r")):
        out[-1] += nl

    start = comments.get(ext).get("start")
    char = comments.get(ext).get("char")
    line = comments.get(ext).get("line")
    end = comments.get(ext).get("end")
    divider = comments.get(ext).get("divider")
    license_start = comments.get(ext).get("license").get("start")
    license_end = comments.get(ext).get("license").get("end")

    # Detect an existing header block at the top of the file (position-agnostic)
    header = _find_header_block(lines, start, end, max_region=max_region)

    # A comment without a copyright, such as a directive, is left as it is in
    # copyright_only styles and the header is written above it
    if header is not None and comments.get(ext)["copyright_only"]:
        if not _comment_has_copyright(lines, header, comments.get(ext)):
            header = None

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
    for statement in _statements(cfg):
        out.append(line_prefix + statement + nl)

    if divider:
        out.append(line_prefix.rstrip() + nl)
    if cfg["license"]["enabled"]:
        if license_start != "":
            out.append(line_prefix + license_start + nl)
        if cfg["license"]["external"] is False:
            out.extend(_license_content(cfg, line_prefix, nl))
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

        # A header of line comments directly followed by another line comment
        # would run into it, so the two are kept apart by an empty line
        if start == end and lines and lines[0].lstrip().startswith(start):
            out.append(nl)

    # Append remaining lines
    out.extend(lines)

    return out


def render_update(cfg, ext, offset, lines, nl, max_region=None):
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
    nl
        Line ending of the lines that are written
    max_region
        Number of lines the header must start in, as in `analyze`

    Returns
    -------
        The new file contents as a list of lines. The input is left untouched.

    """
    out = lines[:offset]
    lines = lines[offset:]

    # Detect header block (position-agnostic) within the configured region.
    # The header is updated in the comment style it is written in, including
    # its divider. Legacy styles have no divider. The license markers always
    # come from the extension, so a license is recognised in every style.
    header_style, header = detect_header(lines, ext, max_region=max_region)
    if header_style is None:
        header_style = comments.get(ext)
    start = header_style["start"]
    char = header_style["char"]
    line = header_style["line"]
    end = header_style["end"]
    divider = header_style.get("divider", False)

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
    start_removed = False
    if header_start_idx is not None and header_end_idx is not None:
        header_slice_end = min(header_end_idx + 1, len(lines))
        for idx in range(header_slice_end - 1, header_start_idx - 1, -1):
            if "Copyright" in lines[idx]:
                lines.pop(idx)
                removed += 1
                start_removed = start_removed or idx == header_start_idx

    legal_entities = cfg["legal"]
    idx = 0
    # Insert copyright lines right after the header start (or at top if no header).
    # A header of line comments may start with the copyright itself, the
    # new copyright lines then take the place of that line.
    insert_at = 0
    if header_start_idx is not None and not start_removed:
        insert_at = header_start_idx + 1
    elif header_start_idx is not None:
        insert_at = header_start_idx

    for lid, statement in enumerate(_statements(cfg)):
        lines.insert(insert_at + lid, line_prefix + statement + nl)
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
            license_lines = []
            if divider:
                license_lines.append(line_prefix.rstrip() + nl)
            license_lines.append(line_prefix + license_start + nl)
            if cfg["license"]["external"] is False:
                license_lines.extend(_license_content(cfg, line_prefix, nl))
            # TODO: Read license file
            license_lines.append(line_prefix + license_end + nl)
            lines[idx + 1 : idx + 1] = license_lines

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
        # Lines such as a shebang or doctype must stay at the top of the file
        offset = count_prologue_lines(lines, comments.get(ext)["prologue"])

        # Header lines take the line ending of the lines the header is or goes
        # in, below the prologue
        nl = _detect_newline(lines[offset:], default=_detect_newline(lines))

        # Determine insert vs update by scanning the header block rather than
        # relying on a fixed line index (SQL and indented headers break that).
        scan_lines = lines[offset:]
        header_style, header = detect_header(scan_lines, ext, max_region=args.region)

        # Only the header is updated, a copyright in any other comment is left
        # as it is. The file is checked as it is, the search region counts
        # its lines.
        outside = _copyrights_outside_header(
            scan_lines, ext, header_style, header, args.region
        )

        # Text on the first line of a block comment is moved to a line of its
        # own, so the header can be handled like every other header
        if header is not None and header_style["start"] != header_style["end"]:
            header_start_idx, header_end_idx, _, _ = header
            idx = offset + header_start_idx
            split = _split_header_start(
                lines[idx], header_style, header_start_idx == header_end_idx, nl
            )
            if split != [lines[idx]]:
                lines = lines[:idx] + split + lines[idx + 1 :]
                scan_lines = lines[offset:]
                header_style, header = detect_header(
                    scan_lines, ext, max_region=args.region
                )

        # The same goes for text on the last line of a block comment
        if header is not None and header[3] is not None:
            idx = offset + header[1]
            split = _split_header_end(lines[idx], header_style, nl)
            if split != [lines[idx]]:
                lines = lines[:idx] + split + lines[idx + 1 :]
                scan_lines = lines[offset:]
                header_style, header = detect_header(
                    scan_lines, ext, max_region=args.region
                )

        if header is None or not _has_copyright(header[2]):
            action = "add"
            new_lines = render_insert(cfg, ext, offset, lines, nl, args.region)

        else:
            action = "update"
            new_lines = render_update(cfg, ext, offset, lines, nl, args.region)

        for statement in outside:
            log.warning(
                f"{path}: a copyright statement outside the header is left "
                f'unchanged: "{statement}"'
            )

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

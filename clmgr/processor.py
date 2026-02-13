"""Processor functions"""

import datetime
import filecmp
import os
import re

from clmgr.template import template, comments


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


def _find_header_block(lines, start, end, max_region=None):
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

    search_upto = len(lines)
    if max_region is not None:
        search_upto = min(search_upto, max_region)

    first_idx = _find_first_non_empty_line_index(lines[:search_upto])
    if first_idx is None:
        return None

    first_line = lines[first_idx]
    if not first_line.lstrip().startswith(start):
        return None

    # Single-line comment style (py/sh): header is a run of comment lines.
    if start == end:
        end_idx = first_idx
        for idx in range(first_idx, search_upto):
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
            body.append(before_end + "\n" if not before_end.endswith("\n") else before_end)
        return first_idx, first_idx, body, first_line

    for idx in range(first_idx + 1, search_upto):
        if end in lines[idx]:
            body = lines[first_idx + 1 : idx]
            return first_idx, idx, body, lines[idx]

    return None


def insert_copyright(cfg, path, ext, offset, args):
    # Define backup
    backup_file = str(path.absolute()) + ".bak"

    # Open source in read_only and backup in write mode
    with open(file=path.absolute(), encoding="utf-8", mode="r") as src_read, open(
        file=backup_file, encoding="utf-8", mode="w"
    ) as src_write:
        # Read lines from source and close it
        lines = src_read.readlines()
        src_read.close()

        # Write offset to new file
        for idx in range(len(lines)):
            if idx < offset:
                src_write.write(lines[idx])

        # Now strip the written offset lines from the source
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
            # to avoid duplication.
            if start == end and header_body_lines:
                first = header_body_lines[0]
                if first.strip() == start:
                    header_body_lines = header_body_lines[1:]

        line_prefix = line
        if header_detected and start != end:
            line_prefix = _infer_line_prefix_from_header_body(header_body_lines, char, line)

        src_write.write(start + "\n")
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
            src_write.write(line_prefix + tmpl + "\n")
            legal_entities_idx += 1

        if divider:
            src_write.write(line_prefix.rstrip() + "\n")
        if cfg["license"]["enabled"]:
            if license_start != "":
                src_write.write(line_prefix + license_start + "\n")
            if cfg["license"]["external"] is False:
                src_write.write(line_prefix + cfg["license"]["content"] + "\n")
            # TODO: Read license file
            if license_end != "":
                src_write.write(line_prefix + license_end + "\n")
            if divider:
                src_write.write(line_prefix.rstrip() + "\n")

        if header_detected:
            # Write user header body as-is, then close the comment.
            src_write.writelines(header_body_lines)
            if header_end_line is not None:
                src_write.write(header_end_line)
                if not header_end_line.endswith("\n"):
                    src_write.write("\n")
            else:
                src_write.write(end + "\n")
        else:
            src_write.write(end + "\n")

        # Write remaining lines
        src_write.writelines(lines)
        src_write.flush()
        src_write.close()

        # Remove original file
        os.replace(backup_file, path.absolute())


def update_copyright(cfg, path, ext, offset, args):
    # Define backup
    backup_file = str(path.absolute()) + ".bak"

    # Open source in read_only and backup in write mode
    with open(file=path.absolute(), encoding="utf-8", mode="r") as src_read, open(
        file=backup_file, encoding="utf-8", mode="w"
    ) as src_write:
        start = comments.get(ext).get("start")
        char = comments.get(ext).get("char")
        line = comments.get(ext).get("line")
        divider = comments.get(ext).get("divider")
        end = comments.get(ext).get("end")

        # Read lines from source and close it
        lines = src_read.readlines()
        src_read.close()

        # Write offset to new file
        for idx in range(len(lines)):
            if idx < offset:
                src_write.write(lines[idx])

        # Now strip the written offset lines from the source
        lines = lines[offset:]

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
            lines.insert(insert_at + lid, line_prefix + tmpl + "\n")
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
                    lines.insert(insert_idx, line_prefix.rstrip() + "\n")
                    insert_idx += 1
                lines.insert(insert_idx, line_prefix + license_start + "\n")
                if cfg["license"]["external"] is False:
                    lines.insert(
                        insert_idx + 1, line_prefix + cfg["license"]["content"] + "\n"
                    )
                # TODO: Read license file
                lines.insert(insert_idx + 2, line_prefix + license_end + "\n")

        # Writes all lines to new file
        src_write.writelines(lines)
        src_write.flush()
        src_write.close()

        result = filecmp.cmp(backup_file, path.absolute(), shallow=False)

        # Remove original file
        os.replace(backup_file, path.absolute())

        return not result


def process_lines(cfg, path, ext, lines, args):
    add = 0
    upd = 0
    utd = 0
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
            header_has_copyright = any("Copyright" in l for l in header_body_lines)

        if not header_has_copyright:
            insert_copyright(cfg, path, ext, offset, args)
            add += 1
        else:
            if update_copyright(cfg, path, ext, offset, args):
                upd += 1
            else:
                utd += 1
    except IndexError:
        pass

    return add, upd, utd

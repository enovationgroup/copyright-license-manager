import datetime
import os

from clmgr.template import template, comments


def insert_copyright(cfg, path, ext, offset, args):
    # Define backup
    backup_file = str(path.absolute()) + ".bak"

    # Open source in read_only and backup in write mode
    with open(path.absolute(), "r") as src_read, open(backup_file, "w") as src_write:
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

        # Get header
        header_detected = 0
        if lines[0].startswith(start):
            lines = lines[1:]
            header_detected = 1

        src_write.write(start + char * (int(args.header_length) - len(start)) + "\n")
        src_write.write(line + "\n")
        legal_entities = cfg["legal"]
        legal_entities_idx = 0
        for legal in legal_entities:
            year = datetime.datetime.now().year

            if legal_entities_idx < len(legal_entities) - 1:
                year = legal_entities[legal_entities_idx + 1]["inception"]

            tmpl = template(
                legal["inception"],
                year,
                legal["name"],
                legal["locality"],
                legal["country"],
            )
            src_write.write(line + " " + tmpl + "\n")
            legal_entities_idx += 1

        src_write.write(line + "\n")
        src_write.write(line + " All rights reserved." + "\n")
        src_write.write(line + "\n")

        if header_detected == 1:
            comment_lines = 0
            for x in range(len(lines)):
                if (
                    lines[x].startswith(start) or lines[x].startswith(char)
                ) and not lines[x].startswith(end):
                    if lines[x].startswith(start):
                        src_write(lines[x])
                    elif lines[x].startswith(char):
                        src_write(start + lines[x].lstrip(start))
                    comment_lines += 1

            # Remove written user comment lines from source
            for x in range(0, comment_lines):
                lines.pop(0)
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
    with open(path.absolute(), "r") as src_read, open(backup_file, "w") as src_write:
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

        # Get header
        if lines[0].startswith(start):
            lines = lines[1:]
            lines.insert(
                0, start + char * (int(args.header_length) - len(start)) + "\n"
            )

        # Get Copyright block
        # This block contains only the copyrightmgr lines
        copyright_block = []
        for x in range(len(lines)):
            if "Copyright" in lines[x] and x <= args.region:
                copyright_block.append(lines[x])
        # Remove the copyrightmgr block lines from the source code
        for y in copyright_block:
            lines.remove(y)

        line = comments.get(ext).get("line")
        legal_entities = cfg["legal"]
        idx = 0
        for lid in range(len(legal_entities)):
            legal = legal_entities[lid]
            year = datetime.datetime.now().year

            if lid < len(legal_entities) - 1:
                year = legal_entities[lid + 1]["inception"]

            tmpl = template(
                legal["inception"],
                year,
                legal["name"],
                legal["locality"],
                legal["country"],
            )
            lines.insert(lid + 2, line + " " + tmpl + "\n")
            idx = lid + 2

        # Check for license
        license_block = 0
        for x in range(len(lines)):
            if "All rights reserved" in lines[x] and x <= args.region:
                license_block = 1

        if license_block == 0:
            lines.insert(idx + 1, line + "\n")
            lines.insert(idx + 2, line + " All rights reserved." + "\n")

        # Writes all lines to new file
        src_write.writelines(lines)
        src_write.flush()
        src_write.close()

        # Remove original file
        os.replace(backup_file, path.absolute())


def process_lines(cfg, path, ext, lines, args):
    add = 0
    upd = 0
    copyright_start = 3
    offset = 0

    try:
        # Java
        # The file should ALWAYS start with the package name
        # This will automatically mean that with the comment seperation lines
        # the first copy right line will always be on line 4
        # the offset will be 1 (the package line)
        if ext.lower() == "java":
            copyright_start = 4
            offset = 1

        # Shell
        # The first line of
        # TODO: Implementation
        if ext.lower() == "sh":
            copyright_start = 4
            offset = 1

        start_idx = lines[copyright_start - 1]
        if "Copyright" not in start_idx:
            insert_copyright(cfg, path, ext, offset, args)
            add += 1
        else:
            update_copyright(cfg, path, ext, offset, args)
            upd += 1
    except IndexError:
        pass

    return add, upd
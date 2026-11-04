"""Source file selection

The include and exclude options of a configuration are glob patterns. They are
matched against the path of a source file relative to the input directory, so a
pattern reads the same way it would in a `.gitignore` file.
"""

import codecs
from functools import lru_cache
import logging
import os
from pathlib import Path, PurePath
import re

from clmgr.template import types

log = logging.getLogger("root")

# Directories that never hold source files of the project, such as the
# packages installed by npm. They are skipped at any depth, whatever the
# include and exclude options are.
SKIPPED_DIRECTORIES = ["node_modules"]


@lru_cache(maxsize=None)
def compile_glob(pattern):
    """Compile a glob pattern into a regular expression

    `fnmatch` is not used here because its `*` also matches a path separator,
    which makes it impossible to distinguish a single directory level from any
    number of them.

    Parameters
    ----------
    pattern
        The glob pattern from the configuration

    Returns
    -------
        The compiled expression, anchored on both ends

    """
    regex = []
    idx = 0
    while idx < len(pattern):
        char = pattern[idx]
        if pattern.startswith("**/", idx):
            regex.append("(?:.*/)?")
            idx += 3
        elif pattern.startswith("**", idx):
            regex.append(".*")
            idx += 2
        elif char == "*":
            regex.append("[^/]*")
            idx += 1
        elif char == "?":
            regex.append("[^/]")
            idx += 1
        elif char == "[":
            end = pattern.find("]", idx + 1)
            if end == -1:
                regex.append(re.escape(char))
                idx += 1
            else:
                group = pattern[idx + 1 : end]
                if group.startswith("!"):
                    group = "^" + group[1:]
                regex.append(f"[{group}]")
                idx = end + 1
        else:
            regex.append(re.escape(char))
            idx += 1

    return re.compile("".join(regex) + r"\Z")


def matches(patterns, path):
    """Whether a relative path matches any of the glob patterns

    A pattern matches the whole relative path, the name of the file, the name
    without its extension, or any of the directories leading to it. That keeps
    a short pattern such as `build` or `Generated` working the way it reads,
    without it having to spell out the full path.

    A pattern starting with a `/` is anchored to the input directory, as in a
    `.gitignore` file: it matches the whole relative path or one of the
    directories leading to it, counted from the input directory. So `/src`
    matches every file in the top level src directory, but not in `lib/src`.

    Parameters
    ----------
    patterns
        Glob patterns from the configuration
    path
        Path of a source file, relative to the input directory

    Returns
    -------
        True when at least one pattern matches

    """
    if not patterns:
        return False

    pure = PurePath(path)
    candidates = [pure.as_posix(), pure.name, pure.stem] + list(pure.parts)
    anchored = [pure.as_posix()] + [
        PurePath(*pure.parts[:depth]).as_posix() for depth in range(1, len(pure.parts))
    ]

    for pattern in patterns:
        if pattern.startswith("/"):
            regex = compile_glob(pattern.lstrip("/"))
            if any(regex.match(candidate) for candidate in anchored):
                return True
            continue

        regex = compile_glob(pattern)
        if any(regex.match(candidate) for candidate in candidates):
            return True

    return False


class SourceError(Exception):
    """Files that the source option assigns to more than one file type"""

    def __init__(self, messages):
        super().__init__("\n".join(messages))
        self.messages = messages


def walk(input_dir, include, exclude):
    """Walk the files of the input directory that the patterns select

    Parameters
    ----------
    input_dir
        The directory to walk
    include
        Glob patterns a file must match, an empty list includes everything
    exclude
        Glob patterns a file must not match

    Returns
    -------
        Tuples (path, relative) of every selected regular file, in a stable
        order, with its path relative to the input directory

    """
    for root, dirs, files in os.walk(input_dir, topdown=True):
        relative_root = os.path.relpath(root, input_dir)

        # Do not descend into excluded directories
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in SKIPPED_DIRECTORIES
            and not matches(exclude, relative(relative_root, d))
        )

        for name in sorted(files):
            # Only a regular file can be read, a broken link or a named pipe
            # cannot, or would block the run
            if not os.path.isfile(os.path.join(root, name)):
                log.debug(f"Skipping {os.path.join(root, name)}, it is not a file")
                continue

            path = relative(relative_root, name)
            if include and not matches(include, path):
                continue
            if matches(exclude, path):
                continue

            yield Path(root, name), path


def extension(path):
    """The extension of a file, lowercase and without the leading dot

    Extensions match regardless of case, so Main.JAVA is a Java file.
    """
    return PurePath(path).suffix.lower()[1:]


# The number of bytes read from the start of a file that an include pattern
# selects, to recognise a binary file and to read the shebang
START_SIZE = 8000

# Options of env that take the next word as their value
ENV_OPTIONS_WITH_VALUE = ["-u", "-C", "-P"]


def interpreter(start):
    """The interpreter the shebang of a file names, without a version number

    `#!/usr/bin/perl5.36`, `#!/usr/bin/env perl` and `#!/usr/bin/env -S perl -w`
    all name `perl`, `#!C:\\Python39\\python.exe` names `python`.

    Parameters
    ----------
    start
        The first bytes of the file

    Returns
    -------
        The name of the interpreter, an empty string when the shebang names
        none, or None when the file does not start with a shebang

    """
    first_line = start.split(b"\n", 1)[0]
    if first_line.startswith(codecs.BOM_UTF8):
        first_line = first_line[len(codecs.BOM_UTF8) :]
    if not first_line.startswith(b"#!"):
        return None

    words = first_line[2:].decode("utf-8", errors="replace").split()
    # env runs the program that follows its options and variables
    if words and program(words[0]) == "env":
        words = words[1:]
        while words and (words[0].startswith("-") or "=" in words[0]):
            option = words.pop(0)
            if option in ENV_OPTIONS_WITH_VALUE:
                words = words[1:]
    if not words:
        return ""

    return re.sub(r"[\d.]+$", "", program(words[0]))


def program(word):
    """The name of the program a path in a shebang runs, without .exe"""
    name = re.split(r"[/\\]", word)[-1]
    return re.sub(r"\.exe$", "", name, flags=re.IGNORECASE)


def type_entries(source):
    """The type entries of the source option, with the definition of each type

    Parameters
    ----------
    source
        The validated source option

    Returns
    -------
        A mapping per type entry, with its type, the extensions and
        interpreters of the type, and its include and exclude patterns

    """
    return [
        {
            "type": entry["type"],
            **types[entry["type"]],
            "include": entry.get("include") or [],
            "exclude": entry.get("exclude") or [],
        }
        for entry in source
        if isinstance(entry, dict)
    ]


def type_extension(entry, ext):
    """The extension whose comment style a file of a type gets

    A file keeps its own extension when it belongs to the type, as the
    extensions of a type may differ in the lines that stay on top. Any other
    file gets the first extension of the type.
    """
    return ext if ext in entry["extensions"] else entry["extensions"][0]


def comment_extension(source, path, file):
    """The extension whose comment style a file gets, by the source option

    An extension listed as a plain value claims every file with that
    extension. An include pattern of a type entry claims the other files it
    matches, and takes precedence over the extensions of the types. A file it
    includes is checked against its shebang: when that names an interpreter
    of a listed type, the file gets that type, any other interpreter leaves
    the file out. Otherwise the file is a source when its extension belongs
    to a listed type that does not exclude it.

    Parameters
    ----------
    source
        The validated source option
    path
        Path of the file, relative to the input directory
    file
        Path of the file, to read its start

    Returns
    -------
        The extension, or None when the file is not a source

    Raises
    ------
    SourceError
        When include patterns of more than one type match a file without a
        shebang

    """
    ext = extension(path)
    if ext in source:
        return ext

    # A type that excludes the file does not get it in any way
    entries = [
        entry for entry in type_entries(source) if not matches(entry["exclude"], path)
    ]

    included = [entry for entry in entries if matches(entry["include"], path)]
    if included:
        with open(file, mode="rb") as src:
            start = src.read(START_SIZE)
        # A NUL byte near the start makes it a binary file, as git decides
        if b"\0" in start:
            log.debug(f"Skipping {path}, it is a binary file")
            return None

        name = interpreter(start)
        if name is not None:
            return shebang_extension(entries, included, path, ext, name)
        if len(included) > 1:
            names = " and ".join(entry["type"] for entry in included)
            raise SourceError(
                [
                    f"{path} is included by the types {names}, "
                    "give it an extension or include it in one type only"
                ]
            )
        return type_extension(included[0], ext)

    for entry in entries:
        if ext in entry["extensions"]:
            return ext

    return None


def shebang_extension(entries, included, path, ext, name):
    """The extension whose comment style a file with a shebang gets

    Parameters
    ----------
    entries
        The type entries of the source option, as `type_entries` returns them
    included
        The entries whose include patterns select the file
    path
        Path of the file, relative to the input directory, for reporting
    ext
        Extension of the file
    name
        The interpreter the shebang names

    Returns
    -------
        The extension for the listed type the interpreter belongs to,
        preferring the types that include the file, or None when it belongs
        to none of them

    """
    named = [entry for entry in entries if name in entry["interpreters"]]
    if not named:
        log.debug(
            f"Skipping {path}, its shebang names {name or 'no interpreter'}, "
            "which runs no type in the source option"
        )
        return None

    # An interpreter may run several types, the include pattern decides
    preferred = [entry for entry in named if entry in included]

    return type_extension((preferred or named)[0], ext)


def select_sources(input_dir, source, include, exclude):
    """Collect the source files to process, by the source option

    Parameters
    ----------
    input_dir
        The directory to walk
    source
        The validated source option
    include
        Glob patterns a file must match, an empty list includes everything
    exclude
        Glob patterns a file must not match

    Returns
    -------
        Tuples (path, ext) of every source file, in a stable order, with the
        extension whose comment style the file gets

    Raises
    ------
    SourceError
        When the source option assigns files to more than one type, after
        reporting every such file

    """
    selected = []
    errors = []
    for path, relative_path in walk(input_dir, include, exclude):
        try:
            ext = comment_extension(source, relative_path, path)
        except SourceError as error:
            errors.extend(error.messages)
            continue
        if ext is not None:
            selected.append((path, ext))

    if errors:
        raise SourceError(errors)

    return selected


def select_file(input_dir, path, source, include, exclude):
    """Select a single file given with -i/--file, by the source option

    The file goes through the same selection as the files of a directory
    walk: the top-level include and exclude patterns, the directories that
    never hold source files, and the patterns of a type. Every pattern is
    matched against the path relative to the input directory. Symbolic links
    are resolved first, so a file given by its real path is found in an input
    directory given by a link, and the other way around.

    Parameters
    ----------
    input_dir
        The input directory
    path
        Path of the file
    source
        The validated source option
    include
        Glob patterns a file must match, an empty list includes everything
    exclude
        Glob patterns a file must not match

    Returns
    -------
        A list with the tuple (path, ext), or an empty list when the file is
        not a source

    Raises
    ------
    SourceError
        When the source option assigns the file to more than one type

    """
    if not path.is_file():
        log.warning(f"Skipping {path}, it is not a file")
        return []

    try:
        relative_path = PurePath(
            os.path.relpath(path.resolve(), Path(input_dir).resolve())
        )
    except ValueError:
        # On Windows a file on another drive has no relative path
        relative_path = PurePath(path.name)

    relative_path = relative_path.as_posix()
    if not selected_by_patterns(relative_path, include, exclude):
        return []

    ext = comment_extension(source, relative_path, path)

    return [] if ext is None else [(path, ext)]


def selected_by_patterns(path, include, exclude):
    """Whether the options of the configuration select a file

    The walk leaves the same files out, silently, because it has no file to
    report. A file given with -i/--file was asked for by name, so the reason
    it is not processed is logged.

    Parameters
    ----------
    path
        Path of the file, relative to the input directory
    include
        Glob patterns a file must match, an empty list includes everything
    exclude
        Glob patterns a file must not match

    Returns
    -------
        True when the file is processed

    """
    for part in PurePath(path).parts[:-1]:
        if part in SKIPPED_DIRECTORIES:
            log.info(f"Skipping {path}, it is in {part}")
            return False

    if include and not matches(include, path):
        log.info(f"Skipping {path}, the include patterns do not select it")
        return False

    if matches(exclude, path):
        log.info(f"Skipping {path}, an exclude pattern takes it out")
        return False

    return True


def relative(relative_root, name):
    """Join a name to the directory it was found in, relative to the input"""
    if relative_root in [".", ""]:
        return name

    return PurePath(relative_root, name).as_posix()

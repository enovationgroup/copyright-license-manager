"""Source file selection

The include and exclude options of a configuration are glob patterns. They are
matched against the path of a source file relative to the input directory, so a
pattern reads the same way it would in a `.gitignore` file.
"""

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
        Tuples (path, relative) of every selected file, in a stable order,
        with its path relative to the input directory

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


def interpreter(file):
    """The interpreter the shebang of a file names, without a version number

    `#!/usr/bin/perl5.36`, `#!/usr/bin/env perl` and `#!/usr/bin/env -S perl -w`
    all name `perl`.

    Parameters
    ----------
    file
        Path of the file

    Returns
    -------
        The name of the interpreter, an empty string when the shebang names
        none, or None when the file does not start with a shebang

    """
    with open(file, mode="rb") as src:
        first_line = src.readline(1024)
    if not first_line.startswith(b"#!"):
        return None

    words = first_line[2:].decode("utf-8", errors="replace").split()
    # env runs the program that follows its options and variables
    if words and words[0].rsplit("/", 1)[-1] == "env":
        words = [w for w in words[1:] if not w.startswith("-") and "=" not in w]
    if not words:
        return ""

    return re.sub(r"[\d.]+$", "", words[0].rsplit("/", 1)[-1])


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


def comment_extension(source, path, file):
    """The extension whose comment style a file gets, by the source option

    An include pattern of a type entry takes precedence over the extension of
    the file. A file it includes is checked against its shebang: when that
    names an interpreter of a listed type, the file gets that type, any other
    interpreter leaves the file out. Otherwise the file is a source when its
    extension is listed, or belongs to a listed type and is not excluded from
    it.

    Parameters
    ----------
    source
        The validated source option
    path
        Path of the file, relative to the input directory
    file
        Path of the file, to read its shebang

    Returns
    -------
        The extension, or None when the file is not a source

    Raises
    ------
    SourceError
        When include patterns of more than one type match a file without a
        shebang

    """
    # A type that excludes the file does not get it in any way
    entries = [
        entry for entry in type_entries(source) if not matches(entry["exclude"], path)
    ]

    included = [entry for entry in entries if matches(entry["include"], path)]
    if included:
        name = interpreter(file)
        if name is not None:
            return shebang_extension(entries, included, path, name)
        if len(included) > 1:
            names = " and ".join(entry["type"] for entry in included)
            raise SourceError(
                [
                    f"{path} is included by the types {names}, "
                    "give it an extension or include it in one type only"
                ]
            )
        return included[0]["extensions"][0]

    ext = extension(path)
    if ext in source:
        return ext
    for entry in entries:
        if ext in entry["extensions"]:
            return ext

    return None


def shebang_extension(entries, included, path, name):
    """The extension whose comment style a file with a shebang gets

    Parameters
    ----------
    entries
        The type entries of the source option, as `type_entries` returns them
    included
        The entries whose include patterns select the file
    path
        Path of the file, relative to the input directory, for reporting
    name
        The interpreter the shebang names

    Returns
    -------
        The first extension of the listed type the interpreter belongs to,
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

    return (preferred or named)[0]["extensions"][0]


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


def select_file(input_dir, path, source):
    """Select a single file given with -i/--file, by the source option

    The include patterns of a type are matched against the path relative to
    the input directory, as when the directory is walked.

    Parameters
    ----------
    input_dir
        The input directory
    path
        Path of the file
    source
        The validated source option

    Returns
    -------
        A list with the tuple (path, ext), or an empty list when the file is
        not a source

    Raises
    ------
    SourceError
        When the source option assigns the file to more than one type

    """
    try:
        relative_path = PurePath(os.path.relpath(path.absolute(), input_dir))
    except ValueError:
        # On Windows a file on another drive has no relative path
        relative_path = PurePath(path.name)

    ext = comment_extension(source, relative_path.as_posix(), path)

    return [] if ext is None else [(path, ext)]


def relative(relative_root, name):
    """Join a name to the directory it was found in, relative to the input"""
    if relative_root in [".", ""]:
        return name

    return PurePath(relative_root, name).as_posix()

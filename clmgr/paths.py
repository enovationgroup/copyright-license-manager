"""Source file selection

The include and exclude options of a configuration are glob patterns. They are
matched against the path of a source file relative to the input directory, so a
pattern reads the same way it would in a `.gitignore` file.
"""

from functools import lru_cache
import os
from pathlib import Path, PurePath
import re

from clmgr.template import types

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
    """A file that the source option assigns to more than one file type"""


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


def select_files(input_dir, ext, include, exclude):
    """Collect the source files of one extension to process

    Parameters
    ----------
    input_dir
        The directory to walk
    ext
        Source file extension, without the leading dot
    include
        Glob patterns a file must match, an empty list includes everything
    exclude
        Glob patterns a file must not match

    Returns
    -------
        The selected paths, in a stable order

    """
    return [
        path
        for path, relative_path in walk(input_dir, include, exclude)
        if extension(relative_path) == ext
    ]


def source_extension(source, path):
    """The extension whose comment style a file gets, by the source option

    An include pattern of a type entry takes precedence over the extension of
    the file. Otherwise the file is a source when its extension is listed, or
    belongs to a listed type and is not excluded from it.

    Parameters
    ----------
    source
        The validated source option
    path
        Path of the file, relative to the input directory

    Returns
    -------
        The extension, or None when the file is not a source

    Raises
    ------
    SourceError
        When include patterns of more than one type match the file

    """
    entries = [entry for entry in source if isinstance(entry, dict)]

    included = [
        entry["type"]
        for entry in entries
        if matches(entry.get("include") or [], path)
        and not matches(entry.get("exclude") or [], path)
    ]
    if len(included) > 1:
        raise SourceError(
            f"{path} is included by the types {' and '.join(included)}, "
            "give it an extension or include it in one type only"
        )
    if included:
        return types[included[0]][0]

    ext = extension(path)
    if ext in source:
        return ext
    for entry in entries:
        if ext in types[entry["type"]] and not matches(
            entry.get("exclude") or [], path
        ):
            return ext

    return None


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
            ext = source_extension(source, relative_path)
        except SourceError as error:
            errors.append(str(error))
            continue
        if ext is not None:
            selected.append((path, ext))

    if errors:
        raise SourceError("\n".join(errors))

    return selected


def relative(relative_root, name):
    """Join a name to the directory it was found in, relative to the input"""
    if relative_root in [".", ""]:
        return name

    return PurePath(relative_root, name).as_posix()

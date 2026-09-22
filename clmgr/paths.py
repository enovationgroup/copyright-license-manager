"""Source file selection

The include and exclude options of a configuration are glob patterns. They are
matched against the path of a source file relative to the input directory, so a
pattern reads the same way it would in a `.gitignore` file.
"""

from functools import lru_cache
import os
from pathlib import Path, PurePath
import re


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

    for pattern in patterns:
        regex = compile_glob(pattern)
        if any(regex.match(candidate) for candidate in candidates):
            return True

    return False


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
    selected = []

    for root, dirs, files in os.walk(input_dir, topdown=True):
        relative_root = os.path.relpath(root, input_dir)

        # Do not descend into excluded directories
        dirs[:] = sorted(
            d for d in dirs if not matches(exclude, relative(relative_root, d))
        )

        for name in sorted(files):
            if not name.endswith("." + ext):
                continue

            path = relative(relative_root, name)
            if include and not matches(include, path):
                continue
            if matches(exclude, path):
                continue

            selected.append(Path(root, name))

    return selected


def relative(relative_root, name):
    """Join a name to the directory it was found in, relative to the input"""
    if relative_root in [".", ""]:
        return name

    return PurePath(relative_root, name).as_posix()

"""Change handler implementations

A run either applies the rendered changes to the source files or only reports
them. That choice is captured in a handler implementation, and the optional
behaviour of --diff and --check is layered on top of it with a decorator, so
neither has to be checked where a change is processed.
"""

from abc import ABC, abstractmethod
import difflib
import sys

from clmgr.processor import write_file


def report(message):
    """Print a line of the human readable report, keeping stdout free"""
    print(message, file=sys.stderr)


def count_of_files(count):
    """Format a number of source files, in singular or plural form"""
    return "1 file" if count == 1 else f"{count} files"


class ChangeHandler(ABC):
    """Processes the outcome for every source file and reports the totals"""

    @abstractmethod
    def handle(self, action, path, lines, new_lines):
        """Process the outcome for a single source file

        Parameters
        ----------
        action
            One of "add", "update" or "none"
        path
            Path of the source file
        lines
            Original file contents
        new_lines
            The contents rendered for this file

        Returns
        -------
            None

        """

    @abstractmethod
    def summarize(self):
        """Print the totals for this run

        Returns
        -------
            None

        """

    @abstractmethod
    def exit_code(self):
        """The exit code for this run

        Returns
        -------
            The exit code

        """


class CountingHandler(ChangeHandler):
    """Base implementation that keeps track of the totals for a run

    Subclasses implement `process`, which is called for every source file.
    """

    added_summary = "added"
    updated_summary = "updated"

    def __init__(self):
        self.added = 0
        self.updated = 0
        self.up_to_date = 0

    def handle(self, action, path, lines, new_lines):
        if action == "add":
            self.added += 1
        elif action == "update":
            self.updated += 1
        else:
            self.up_to_date += 1

        self.process(action, path, lines, new_lines)

    @abstractmethod
    def process(self, action, path, lines, new_lines):
        """Process a single source file"""

    def summarize(self):
        report(f"{count_of_files(self.added)}: Copyright {self.added_summary}")
        report(f"{count_of_files(self.updated)}: Copyright {self.updated_summary}")
        report(f"{count_of_files(self.up_to_date)}: Copyright up to date")

    def exit_code(self):
        return 0


class ApplyHandler(CountingHandler):
    """Writes the rendered contents to the source files"""

    def process(self, action, path, lines, new_lines):
        if action != "none":
            write_file(path, new_lines)


class DryRunHandler(CountingHandler):
    """Reports the state of every source file without modifying any of them"""

    added_summary = "would be added"
    updated_summary = "would be updated"

    labels = {
        "add": "would add to",
        "update": "would update",
        "none": "up to date",
    }

    def process(self, action, path, lines, new_lines):
        report(f"{self.labels[action]:<12} {path}")


class ChangeHandlerDecorator(ChangeHandler):
    """Base implementation for handlers that extend another handler"""

    def __init__(self, handler):
        self.handler = handler

    def handle(self, action, path, lines, new_lines):
        self.handler.handle(action, path, lines, new_lines)

    def summarize(self):
        self.handler.summarize()

    def exit_code(self):
        return self.handler.exit_code()


class DiffHandler(ChangeHandlerDecorator):
    """Prints a unified diff for every source file that is not up to date"""

    def handle(self, action, path, lines, new_lines):
        super().handle(action, path, lines, new_lines)

        if action != "none":
            sys.stdout.writelines(
                difflib.unified_diff(
                    lines, new_lines, fromfile=str(path), tofile=str(path)
                )
            )


class CheckHandler(ChangeHandlerDecorator):
    """Fails the run when a source file is not up to date"""

    def __init__(self, handler):
        super().__init__(handler)
        self.changed = 0

    def handle(self, action, path, lines, new_lines):
        super().handle(action, path, lines, new_lines)

        if action != "none":
            self.changed += 1

    def exit_code(self):
        if self.changed > 0:
            return 1

        return 0


def create_handler(args):
    """Create the change handler matching the commandline arguments

    A --check run reports without modifying any file, so it implies --dry-run.
    A --diff run is verbose about the changes it reports, whether or not those
    changes are applied.

    Parameters
    ----------
    args
        Parsed commandline arguments

    Returns
    -------
        The change handler for this run

    """
    if args.dry_run or args.check:
        handler = DryRunHandler()
    else:
        handler = ApplyHandler()

    if args.diff:
        handler = DiffHandler(handler)
    if args.check:
        handler = CheckHandler(handler)

    return handler

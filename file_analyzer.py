"""Display line, word, and character counts for a UTF-8 text file."""

import argparse
import os
import sys
from typing import NamedTuple


class FileStats(NamedTuple):
    lines: int
    words: int
    characters: int


class AnalysisError(Exception):
    """A problem with the file, described in words the user can act on."""


def analyze_file(path):
    """Return the statistics for a file, or raise AnalysisError."""
    # Checked first because Windows reports opening a directory as "permission denied".
    if os.path.isdir(path):
        raise AnalysisError(f"'{path}' is a directory. Please provide a file.")

    lines = words = characters = 0
    try:
        # utf-8-sig drops a leading BOM. newline=None turns \r\n and \r into \n.
        with open(path, encoding="utf-8-sig", newline=None) as file:
            for line in file:
                if "\0" in line:
                    raise AnalysisError(
                        f"'{path}' appears to be binary or not UTF-8 text."
                    )
                lines += 1
                words += len(line.split())
                characters += len(line)
    except FileNotFoundError:
        raise AnalysisError(f"'{path}' was not found. Check the path and try again.")
    except PermissionError:
        raise AnalysisError(f"Permission denied when reading '{path}'.")
    except UnicodeDecodeError:
        raise AnalysisError(
            f"'{path}' is not valid UTF-8. Only UTF-8 text is supported."
        )
    except OSError as error:
        raise AnalysisError(f"Could not read '{path}': {error.strerror or error}.")
    except MemoryError:
        raise AnalysisError(f"Could not read '{path}': not enough memory.")

    return FileStats(lines, words, characters)


def format_report(path, stats):
    """Return the report that is shown to the user."""
    return (
        f"File:       {path}\n"
        f"Lines:      {stats.lines}\n"
        f"Words:      {stats.words}\n"
        f"Characters: {stats.characters}"
    )


def main(argv=None):
    """Run the command-line program and return its exit code."""
    parser = argparse.ArgumentParser(
        prog="file_analyzer.py",
        description="Count the lines, words, and characters in a UTF-8 text file.",
    )
    parser.add_argument("file_path", help="path of the text file to analyze")
    args = parser.parse_args(argv)  # Exits with code 2 if the arguments are wrong.

    try:
        stats = analyze_file(args.file_path)
    except AnalysisError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    try:
        print(format_report(args.file_path, stats), flush=True)
    except OSError:
        print("Error: Could not write the results.", file=sys.stderr)
        # Discard unwritten output, or Python fails again when it flushes at exit.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 1

    return 0


if __name__ == "__main__":
    # A file name the terminal cannot encode should not crash the report.
    if sys.stdout is not None:
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())

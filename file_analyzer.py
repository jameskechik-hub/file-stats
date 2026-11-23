"""Display line, word, and character counts for one or more UTF-8 text files."""

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


def format_counts(stats):
    """Return the count lines shared by file reports and totals."""
    return (
        f"Lines:      {stats.lines}\n"
        f"Words:      {stats.words}\n"
        f"Characters: {stats.characters}"
    )


def format_report(path, stats):
    """Return the report for one file."""
    return f"File:       {path}\n" + format_counts(stats)


def format_totals(file_count, stats):
    """Return the combined totals for the files that were analyzed."""
    noun = "file" if file_count == 1 else "files"
    return f"Total ({file_count} {noun})\n" + format_counts(stats)


def add_stats(first, second):
    """Return the sum of two sets of statistics."""
    return FileStats(*(a + b for a, b in zip(first, second)))


def write_block(text, first):
    """Write one block to stdout, after a blank line unless it is the first.

    Return False if the output could not be written.
    """
    try:
        print(text if first else "\n" + text, flush=True)
    except OSError:
        print("Error: Could not write the results.", file=sys.stderr)
        # Discard unwritten output, or Python fails again when it flushes at exit.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return False
    return True


def main(argv=None):
    """Run the command-line program and return its exit code."""
    parser = argparse.ArgumentParser(
        prog="file_analyzer.py",
        description="Count the lines, words, and characters in UTF-8 text files.",
    )
    parser.add_argument(
        "file_paths",
        nargs="+",
        metavar="file_path",
        help="path of a text file to analyze",
    )
    args = parser.parse_args(argv)  # Exits with code 2 if the arguments are wrong.

    total = FileStats(0, 0, 0)
    analyzed = 0
    any_failed = False

    for path in args.file_paths:
        try:
            stats = analyze_file(path)
        except AnalysisError as error:
            print(f"Error: {error}", file=sys.stderr, flush=True)
            any_failed = True
            continue  # R11: report the error and go on to the next file.

        if not write_block(format_report(path, stats), first=analyzed == 0):
            return 1
        analyzed += 1
        total = add_stats(total, stats)

    # R12: totals only make sense when more than one path was given.
    if len(args.file_paths) > 1:
        if not write_block(format_totals(analyzed, total), first=analyzed == 0):
            return 1

    return 1 if any_failed else 0


if __name__ == "__main__":
    # A file name the terminal cannot encode should not crash the report.
    if sys.stdout is not None:
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())

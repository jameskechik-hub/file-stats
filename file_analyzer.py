"""Display line, word, and character counts and the longest word for UTF-8 text files.

A directory path analyzes the .txt files directly inside it.
With --summary-only, only the combined totals and file counts are shown.
"""

import argparse
import os
import sys
from typing import NamedTuple


class FileStats(NamedTuple):
    lines: int
    words: int
    characters: int
    longest_word: str = ""  # Empty when the file has no words (R16).


class AnalysisError(Exception):
    """A problem with the file, described in words the user can act on."""


def analyze_file(path):
    """Return the statistics for a file, or raise AnalysisError."""
    # Checked first because Windows reports opening a directory as "permission denied".
    if os.path.isdir(path):
        raise AnalysisError(f"'{path}' is a directory. Please provide a file.")

    lines = words = characters = 0
    longest_word = ""
    try:
        # utf-8-sig drops a leading BOM. newline=None turns \r\n and \r into \n.
        with open(path, encoding="utf-8-sig", newline=None) as file:
            for line in file:
                if "\0" in line:
                    raise AnalysisError(
                        f"'{path}' appears to be binary or not UTF-8 text."
                    )
                line_words = line.split()
                lines += 1
                words += len(line_words)
                characters += len(line)
                for word in line_words:
                    # Strictly longer, so the first of several equal words is kept (R15).
                    if len(word) > len(longest_word):
                        longest_word = word
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

    return FileStats(lines, words, characters, longest_word)


def list_text_files(directory):
    """Return the paths of the .txt files directly inside a directory (R19, R20).

    Only regular files whose names end in .txt, ignoring case, are included.
    Subdirectories are not searched. The paths are sorted by file name, ignoring
    case, with the exact name breaking ties so the order is always the same.
    Raise AnalysisError if the directory cannot be listed.
    """
    try:
        with os.scandir(directory) as entries:
            names = [
                entry.name
                for entry in entries
                if entry.name.lower().endswith(".txt") and entry.is_file()
            ]
    except PermissionError:
        raise AnalysisError(f"Permission denied when reading directory '{directory}'.")
    except OSError as error:
        raise AnalysisError(
            f"Could not read directory '{directory}': {error.strerror or error}."
        )

    names.sort(key=lambda name: (name.casefold(), name))
    return [os.path.join(directory, name) for name in names]


def format_counts(stats):
    """Return the count lines shared by file reports and totals."""
    return (
        f"Lines:      {stats.lines}\n"
        f"Words:      {stats.words}\n"
        f"Characters: {stats.characters}"
    )


def format_longest(word):
    """Return the longest-word line, or N/A with a length of 0 if there is none."""
    if not word:
        return "Longest:    N/A (0 characters)"
    noun = "character" if len(word) == 1 else "characters"
    return f"Longest:    {word} ({len(word)} {noun})"


def format_report(path, stats):
    """Return the report for one file."""
    return (
        f"File:       {path}\n"
        + format_counts(stats)
        + "\n"
        + format_longest(stats.longest_word)
    )


def format_totals(succeeded, failed, stats):
    """Return the final summary: combined totals and the file counts."""
    noun = "file" if succeeded == 1 else "files"
    return (
        f"Total ({succeeded} {noun})\n"
        + format_counts(stats)
        + f"\nSucceeded:  {succeeded}"  # R17
        + f"\nFailed:     {failed}"  # R18
    )


def add_stats(first, second):
    """Return the summed counts of two sets of statistics.

    The totals have no longest word, so it is left empty.
    """
    return FileStats(
        first.lines + second.lines,
        first.words + second.words,
        first.characters + second.characters,
    )


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
        # Written out because nargs="*" would show the paths as optional.
        usage="%(prog)s [-h] [--summary-only] file_path [file_path ...]",
        description=(
            "Count the lines, words, and characters in UTF-8 text files "
            "and find the longest word in each. A directory analyzes the "
            ".txt files directly inside it, in alphabetical order."
        ),
        allow_abbrev=False,  # Only the exact --summary-only is accepted.
    )
    parser.add_argument(
        "file_paths",
        nargs="*",  # At least one is required; checked below for a clearer message.
        metavar="file_path",
        help="path of a text file, or of a directory whose .txt files to analyze",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="show only the combined totals and file counts, not each file",
    )
    # Intermixed, so the flag may come before, after, or between the paths (R24).
    # Exits with code 2 if the arguments are wrong.
    args = parser.parse_intermixed_args(argv)
    if not args.file_paths:
        if args.summary_only:  # R28
            parser.error("--summary-only requires at least one file or directory path.")
        parser.error("the following arguments are required: file_path")

    total = FileStats(0, 0, 0)
    analyzed = 0
    failed = 0
    any_directory = False

    for argument in args.file_paths:
        # R19: a directory is replaced, in place, by the .txt files inside it.
        if os.path.isdir(argument):
            any_directory = True
            try:
                paths = list_text_files(argument)
            except AnalysisError as error:
                print(f"Error: {error}", file=sys.stderr, flush=True)
                failed += 1
                continue  # R23: a directory that cannot be listed is one failure.
        else:
            paths = [argument]

        for path in paths:
            try:
                stats = analyze_file(path)
            except AnalysisError as error:
                print(f"Error: {error}", file=sys.stderr, flush=True)
                failed += 1
                continue  # R11, R23: report the error and go on to the next file.

            # R25: with --summary-only, file blocks are left out.
            if not args.summary_only:
                if not write_block(format_report(path, stats), first=analyzed == 0):
                    return 1
            analyzed += 1
            total = add_stats(total, stats)

    # R11, R12, R22: a summary for several paths, or for any directory.
    # R25: --summary-only always shows it, even for a single file.
    if args.summary_only or len(args.file_paths) > 1 or any_directory:
        summary = format_totals(analyzed, failed, total)
        if not write_block(summary, first=args.summary_only or analyzed == 0):
            return 1

    return 1 if failed else 0


if __name__ == "__main__":
    # A file name the terminal cannot encode should not crash the report.
    if sys.stdout is not None:
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())

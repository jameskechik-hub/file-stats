# 0008: Make --summary-only hide the file blocks but keep the summary, errors, and exit codes

- Status: Accepted
- Date: 2026-11-22
- Requirements: R1, R6, R11, R12, R22, R24, R25, R26, R27, R28
- Extends: [0004](0004-multi-file-output-layout.md), [0006](0006-success-and-failure-counts.md), [0007](0007-directory-analysis.md)

## Y-statement

**In the context of** Round 6, which adds an optional `--summary-only` flag that shows only the combined statistics (R24, R25), must leave the output unchanged without the flag (R26), must work with files, directories, and mixes of them (R27), and must give a helpful error when no paths are given (R28),

**facing** an R12/R22 rule that shows no summary for a single file path, error messages on stderr that are not "statistics", argparse's default behavior of rejecting an option placed between positional paths, and a generic "required: file_path" message that does not mention the flag,

**we decided for** keeping the one analysis loop and simply not printing file blocks when the flag is set, always printing the unchanged Round 4 summary block when the flag is set (so a single file gets `Total (1 file)`), still writing every error to stderr, keeping all exit codes, parsing arguments with `parse_intermixed_args` so the flag can appear anywhere, turning off option abbreviations, and treating the flag without paths as a usage error (exit 2) with the message `--summary-only requires at least one file or directory path.`,

**and neglected** printing nothing for a single file, a new summary format just for this mode, hiding error messages, accepting the flag only before the paths, allowing abbreviations such as `--summary`, using argparse's generic "required" message, and treating the missing paths as a file error with exit code 1,

**to achieve** a summary that is identical, line for line, to the end of the normal output, so scripts can read the same last two lines in both modes; one code path, so files, directories, failures, and counts behave the same with and without the flag; a flag that "just works" wherever it is typed; and output without the flag that is identical to Rounds 1-5,

**accepting that** a single file path now shows a summary in one mode but not the other, that stdout alone does not say which files failed (stderr and `Failed:` do), that the `usage:` line is written out by hand because the paths are now checked in code, and that a file literally named `--summary-only` must be given as `./--summary-only` (or after `--`).

## Notes

- The user chose these before any code was written: a single file shows the summary, errors stay on stderr, the flag may appear anywhere, and the flag without paths exits with 2 and a specific message.
- Decided without asking: the flag given twice is the same as once; abbreviations are turned off; with no arguments at all, the Round 1 message `the following arguments are required: file_path` is kept exactly; the help text lists the flag; the summary has no blank line before it.
- The paths use `nargs="*"` and are checked after parsing, because with `nargs="+"` argparse would print its generic message before the program could add the R28 message. The usage line is set by hand so it still reads `file_path [file_path ...]`, which earlier tests check.
- If stdout cannot be written, the program still stops with exit code 1, as in [0003](0003-continue-after-file-errors.md).

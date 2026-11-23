# 0007: Expand a directory in place into its .txt files, sorted ignoring case

- Status: Accepted
- Date: 2026-11-22
- Requirements: R6, R9, R11, R12, R19, R20, R21, R22, R23
- Extends: [0003](0003-continue-after-file-errors.md), [0004](0004-multi-file-output-layout.md), [0006](0006-success-and-failure-counts.md)

## Y-statement

**In the context of** Round 5, which requires analyzing every regular `.txt` file directly inside a directory given on the command line, in alphabetical order, with the existing per-file blocks, totals, and success/failure counts (R19-R23),

**facing** an R6 rule that rejected directories, a summary that was shown only for two or more paths, and open questions about mixing directories with files, empty directories, how to label files found in a directory, and letter case on Windows,

**we decided for** replacing each directory argument, in place, with the paths of its regular `.txt` files (matched and sorted ignoring case, with the exact name breaking ties), joining the directory as typed with each file name for the `File:` line, sending every file through the unchanged analysis, error, and counting code, showing the summary whenever any argument is a directory (so an empty directory prints a zero summary and exits with 0), and counting a directory that cannot be listed as one failure,

**and neglected** allowing only a single directory with nothing else, recursive search, a separate summary per directory, showing only the bare file name, case-sensitive matching and sorting, "natural" number-aware sorting, and treating an empty directory as an error,

**to achieve** one code path for files no matter how they were named, so multiple-file analysis, longest words, and the Round 4 counts keep working, plus output that tells apart files from different directories, an order that is the same on every system, and single-file output that is identical to Rounds 1-4,

**accepting that** a directory no longer gives the Round 1 "is a directory" error, that `Succeeded + Failed` no longer equals the number of arguments, that `10.txt` sorts before `2.txt`, that the path separator in the `File:` line depends on the operating system, and that a broken symbolic link ending in `.txt` is skipped without a message.

## Notes

- The user chose these before any code was written: directories can be mixed with files and other directories, a directory always gets a summary (an empty one is not an error), the `File:` line joins the directory with the file name, and `.txt` matching and sorting ignore case.
- Decided without asking: hidden files such as `.notes.txt` and a file named exactly `.txt` are included; files with other extensions and subdirectories (even `old.txt/`) are ignored silently and not counted; a symbolic link to a regular file is included; sorting compares characters, not numbers; the directory listing errors use their own messages (`Permission denied when reading directory '...'`, `Could not read directory '...': <reason>`).
- `analyze_file` still rejects a directory, because `main` expands directories before calling it. This only matters if a file is replaced by a directory between listing and reading.
- A file found through a directory and also given directly is analyzed and counted twice, matching R9's rule for repeated paths.

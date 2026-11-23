# 0004: Repeat the Round 1 block for each file and add a totals block

- Status: Accepted
- Date: 2026-11-22
- Requirements: R5, R10, R12

## Y-statement

**In the context of** showing statistics for several files and their combined totals in a terminal,

**facing** the Round 1 output format (R5), which users and tests already depend on, and the risk of totals that are confusing when some files failed,

**we decided for** printing the unchanged Round 1 block for each analyzed file, separated by blank lines, followed by a `Total (N files)` block only when two or more paths are given, where N counts the files that were analyzed successfully,

**and neglected** a `wc`-style table with one row per file, a totals block for a single path, and a header counting every path given,

**to achieve** single-path output that is identical to Round 1, a format that reads the same for one file or many, and totals whose meaning is stated on screen,

**accepting that** many files produce long output that is harder to compare side by side than a table, and that a totals block appears (with `0 files` and zeros) even when every file failed.

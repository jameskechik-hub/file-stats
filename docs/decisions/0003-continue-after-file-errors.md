# 0003: Keep going after a file error, but exit with code 1

- Status: Accepted
- Date: 2026-11-22
- Requirements: R6, R11

## Y-statement

**In the context of** analyzing several files in one command, where some paths may be missing, unreadable, or not UTF-8,

**facing** the need to show results for the good files (R11) while still letting scripts and users notice that something went wrong,

**we decided for** reporting each failed file on stderr with its Round 1 error message, skipping it, finishing the remaining files and the totals, and then returning exit code 1 if any file failed,

**and neglected** stopping at the first bad file, returning 0 whenever at least one file succeeded, and always returning 0 once the arguments were valid,

**to achieve** complete output for every readable file, the same behavior as familiar tools such as `wc`, and an exit code that a script can trust,

**accepting that** a command can print useful results and still "fail", and that the exit code does not say how many files failed (the stderr messages do).

## Notes

- Usage errors (no paths, unknown option) still stop before any file is read and return 2, as in Round 1.
- If stdout cannot be written, processing stops at once with code 1, because there is nowhere to show further results.

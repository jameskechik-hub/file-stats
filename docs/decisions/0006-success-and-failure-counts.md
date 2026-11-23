# 0006: Add success and failure counts to the end of the totals block

- Status: Accepted
- Date: 2026-11-22
- Requirements: R11 (revised), R12, R17, R18
- Extends: [0003](0003-continue-after-file-errors.md), [0004](0004-multi-file-output-layout.md)

## Y-statement

**In the context of** the Round 4 revision of R11, which keeps "continue after a failed file and show its error" but now also requires the final summary to report how many files succeeded and how many failed (R17, R18),

**facing** a summary (the R12 `Total (N files)` block) that already showed the success count only in its header, never showed the failure count, and left users to count stderr lines, as decision 0003 noted ("the exit code does not say how many files failed"),

**we decided for** keeping the R12 totals block as the one final summary and adding two aligned lines at its end, `Succeeded:  N` and `Failed:     M`, always showing both (including `Failed:     0`), and still showing the summary only when two or more paths are given,

**and neglected** putting the counts in the header (`Total (2 succeeded, 1 failed)`), printing a separate counts block after the totals, renaming the block to `Summary` with the counts first, showing a summary for a single path, showing `Failed:` only when something failed, and putting the failure count in the exit code,

**to achieve** explicit, labeled counts that a user can read and a script can find on the last two lines, an unchanged header and count lines for anyone who already reads the totals, single-path output that is still identical to Rounds 1-3, and a very small code change,

**accepting that** the success count now appears twice (in the header and on the `Succeeded:` line), that the summary is two lines longer even when nothing failed, and that a single failed path still reports its failure only through stderr and exit code 1.

## R11 before and after

| | Round 2 R11 | Round 4 R11 |
|---|---|---|
| Trigger | "If one file cannot be read" | "When analyzing multiple files ... an individual file fails" |
| Continue with the other files | Yes | Yes (unchanged) |
| Error for each failed file | "report the error" | "display an error for each failed file" (same behavior) |
| Counts in the final summary | Not required | Successes and failures required |

The behavior on stderr and the exit codes did not change. Only the summary on stdout did.

## Alternatives in more detail

- **Counts in the header:** the shortest change, but the counts would not be labeled lines, the `1 file`/`N files` wording would become harder to read, and every existing test that checks the header would change.
- **Separate block:** leaves R12 completely untouched, but splits "the final summary" into two blocks and adds a second blank-line separator.
- **Rename to `Summary`:** the cleanest layout if starting over, but it changes the R12 header that users and tests already depend on.
- **Summary for one path:** R11 says "when analyzing multiple files", and R10 promises that single-path output is unchanged, so this was rejected.
- **Exit code = number of failures:** would hide failures above 255 and break the R6/R11 rule that 1 means "something failed" and 2 means "usage error".

## Notes

- The user chose the layout ("add two lines") and "no summary for a single path" before any code was written.
- A file counts as failed when it produces any R6 file error. A path given twice counts twice, so `Succeeded + Failed` always equals the number of paths.
- If stdout cannot be written, processing still stops at once with code 1 and no summary, as in 0003.

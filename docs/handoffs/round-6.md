# Handoff: Round 6 (Summary-Only Reporting)

- Date: 2026-11-22
- Branch: `main`
- Last Round 6 implementation commit: `2705f10` (pushed to `origin/main` together with this handoff)
- Test status: 199 tests, 198 passing, 1 skipped, none failing (`python -m unittest`, Python 3.13.7 on Windows). The skipped test is `TestR19DirectoryInput.test_symbolic_link_to_a_file_is_included_and_broken_link_skipped`, which skips itself when the system does not allow creating symbolic links (this Windows account cannot without Developer Mode or administrator rights). Symbolic link behavior has therefore still not been verified on this machine.
- Round 6 is the final development round of the project.

## What Round 6 asked for

From problem.md (committed by the user in `8cc789b`):

- **R24:** The program must accept an optional --summary-only command-line flag.
- **R25:** When --summary-only is provided, the program must display only the combined statistics, including total lines, words, characters, successful files, and failed files. Individual file statistics must be omitted.
- **R26:** When --summary-only is not provided, the program must preserve its existing output behavior.
- **R27:** The --summary-only flag must work with individual files, multiple files, directories, and combinations of file and directory paths.
- **R28:** The program must display a helpful error message if --summary-only is provided without any file or directory paths.

## Conflict with earlier requirements

R12 and R22 show the final summary only when two or more paths are given or any path is a directory, so a single file path gets no summary. R25 requires the combined statistics whenever `--summary-only` is given. This was raised with the user before any code was written, and the user **explicitly chose** to always show the summary with the flag, including for a single file.

## Changes to earlier requirements

No earlier requirement text was rewritten. spec.md adds "Changed in Round 6" notes instead:

- **R1 (Input):** R24 adds the optional `--summary-only` flag. The usage line is now `file_analyzer.py [-h] [--summary-only] file_path [file_path ...]`.
- **R12 (Combined totals):** with `--summary-only`, the totals block is always shown, even for a single file path, and the file blocks are not. Without the flag, R12 and R22 apply exactly as before.
- **R6 / R11 / R23 (Errors):** unchanged. Errors still go to stderr in both modes, and exit codes are unchanged. `--summary-only` without paths is a new usage error (exit 2).

No earlier tests were changed. All 165 tests from Rounds 1-5 still pass (164 passing, 1 skipped, as at the end of Round 5).

## What was done

| Commit | Change |
|---|---|
| `8cc789b` | (User) problem.md: Round 6 requirements R24-R28. |
| `664547b` | spec.md: added R24-R28 to the requirements list, a "Round 6 Details" section with rules, examples, and the user's answers, "Changed in Round 6" notes under R1 and R12, and R24-R28 in the Testing line. |
| `363b57f` | Tests, written before the code. New classes `TestR24SummaryOnlyFlag` (8), `TestR25OnlyCombinedStatistics` (8), `TestR26OutputWithoutFlag` (5), `TestR27SummaryOnlyWithAllPathKinds` (9), `TestR28SummaryOnlyWithoutPaths` (4): 34 tests. Before the implementation, 28 failed as expected; the 6 that passed guard existing behavior (no-flag output, abbreviation rejected, `./--summary-only` file). |
| `2a1bf26` | `file_analyzer.py`: the `--summary-only` flag. |
| `a81103d` | Decision record 0008. |
| `2705f10` | README: "Show only the summary" section with usage, an example, and rules; R24-R28 test classes; link to 0008; exit code 2 row mentions the no-paths case. |
| (this commit) | This handoff file. |

### Files created or modified in Round 6

| File | Status |
|---|---|
| `spec.md` | Modified |
| `tests/test_file_analyzer.py` | Modified (new classes appended; earlier tests unchanged except the module docstring now says R1-R6, R9-R28) |
| `file_analyzer.py` | Modified |
| `docs/decisions/0008-summary-only-flag.md` | Created |
| `README.md` | Modified |
| `docs/handoffs/round-6.md` | Created (this file) |

## Behavior agreed with the user

Asked and answered before any code was written:

1. **Single file:** with `--summary-only`, the summary is always shown, even for one file path (`Total (1 file)`). A single missing file prints `Total (0 files)` with `Failed:     1`.
2. **Errors:** per-file and directory errors are still written to stderr. Only stdout is reduced to the summary.
3. **No paths (R28):** usage error, exit code 2, the usage line, and `file_analyzer.py: error: --summary-only requires at least one file or directory path.`
4. **Position:** the flag may come before, after, or between the paths.

Example (`python file_analyzer.py --summary-only a.txt missing.txt b.txt`, where `a.txt` contains `one two\nthree\n` and `b.txt` contains `four`):

```text
Total (2 files)
Lines:      3
Words:      4
Characters: 18
Succeeded:  2
Failed:     1
```

stderr: `Error: 'missing.txt' was not found. Check the path and try again.` Exit code 1.

## Decision record 0008 and its trade-offs

[0008: Make --summary-only hide the file blocks but keep the summary, errors, and exit codes](../decisions/0008-summary-only-flag.md)

- **Decided for:** one analysis loop that skips printing file blocks when the flag is set; always printing the unchanged Round 4 summary block with the flag; errors still on stderr; exit codes unchanged; `parse_intermixed_args` so the flag can go anywhere; abbreviations off; flag without paths is a usage error (exit 2) with a specific message.
- **Neglected:** printing nothing for a single file, a separate summary format, hiding errors, accepting the flag only before paths, allowing abbreviations, argparse's generic "required" message, and exit code 1 for missing paths.
- **Achieves:** a summary identical, line for line, to the end of the normal output (scripts can read the same last two lines in both modes); one code path for files, directories, failures, and counts; output without the flag identical to Rounds 1-5.
- **Accepts:** a single file path shows a summary in one mode but not the other; stdout alone does not say which files failed; the `usage:` line is written by hand; a file literally named `--summary-only` must be given as `./--summary-only` (or after `--`).

## Decisions made without being asked

- Giving `--summary-only` more than once is the same as giving it once.
- Option abbreviations are turned off (`allow_abbrev=False`), so `--summary` is an unknown option (exit 2).
- With no arguments at all, the Round 1 message `the following arguments are required: file_path` is kept exactly.
- In summary-only mode, the summary has the exact Round 4 format and no blank line before it.
- The help text lists the flag: `show only the combined totals and file counts, not each file`.
- Paths use `nargs="*"` and are checked in code after parsing, so R28 can have its own message. The usage line is set by hand so it still reads `file_path [file_path ...]`, which R1 and R9 tests check.
- If stdout cannot be written, the program still stops at once with exit code 1 (decision 0003).
- A file named `--summary-only` can be analyzed as `./--summary-only`, matching the existing advice for dash-prefixed names.
- All exit codes are unchanged: 0 when nothing failed, 1 when any file or directory failed or output could not be written, 2 for usage errors.
- Commits were made after each step because the user's Round 6 instructions asked for them.

## Code map

- `file_analyzer.py`
  - `main`: the parser now has `usage=` written out, `allow_abbrev=False`, `file_paths` with `nargs="*"`, and a `--summary-only` `store_true` option. Arguments are parsed with `parser.parse_intermixed_args(argv)`. If no paths are given, `parser.error(...)` shows the R28 message when the flag is set, or the Round 1 "required: file_path" message otherwise.
  - In the analysis loop, `write_block(format_report(...))` is skipped when `args.summary_only` is true; counting and totals are unchanged.
  - The summary is shown when `args.summary_only or len(args.file_paths) > 1 or any_directory`, and is written as the first block when the flag is set.
  - `FileStats`, `analyze_file`, `list_text_files`, `format_counts`, `format_longest`, `format_report`, `format_totals`, `add_stats`, `write_block`: unchanged.
- `tests/test_file_analyzer.py`
  - New constants `FLAG` and `NO_PATHS_MESSAGE`.
  - New base class `SummaryOnlyTestCase` (extends `DirectoryTestCase`; adds `a.txt` and `b.txt` next to `notes`) with `assert_only_summary()`, which checks the exit code, that stdout equals the expected summary, and that no `File:` or `Longest:` line appears.
  - Mocks: `os.scandir` (directory that cannot be listed) and `file_analyzer.analyze_file` (to prove nothing is analyzed in the R28 case).

## Decision records

- 0001: Counting rules (Round 1)
- 0002: UTF-8 only (Round 1)
- 0003: Continue after file errors, but exit with code 1 (Round 2)
- 0004: Repeat the Round 1 block per file and add a totals block (Round 2)
- 0005: Longest word rules and one-line layout (Round 3)
- 0006: Success and failure counts at the end of the totals block (Round 4)
- 0007: Expand a directory in place into its .txt files, sorted ignoring case (Round 5)
- 0008: `--summary-only` hides the file blocks but keeps the summary, errors, and exit codes (Round 6)

## Known issues and limitations

- A single file path shows a summary with `--summary-only` but not without it (by the user's choice, but the modes differ).
- In summary-only mode, stdout does not say which files failed; only stderr and the `Failed:` count do.
- The usage line is hand-written, so it must be updated if another option is ever added.
- The symbolic link test is skipped on this machine, so symlink handling is untested here.
- Carried over from Round 5: the path separator in output depends on the operating system; sorting compares characters, so `10.txt` comes before `2.txt`; a broken `.txt` symbolic link is skipped with no message; `Succeeded + Failed` equals files tried plus unlistable directories, not the number of arguments; if a listed file is replaced by a directory before it is read, the old "is a directory" error is shown.
- Git prints harmless "LF will be replaced by CRLF" warnings on commit.

## Open questions

- From Round 5: the user has not explicitly confirmed that R19 replaces the R6 "path is a directory" error (it was stated before coding and not objected to).
- None new in Round 6. All four Round 6 questions were answered before coding.

## Final project status

- All requirements R1-R6 and R9-R28 are implemented and each has at least one automated test class (numbers 7 and 8 are unused, as recorded in spec.md).
- Full suite: 199 tests, 198 passed, 0 failed, 1 skipped.
- Only the Python standard library is used. There is nothing to install.

## How to review the repository

1. Clone or pull `main`, then from the project root run `python -m unittest` (add `-v` to see each test). Expect 199 tests, OK, 1 skipped on systems that cannot create symbolic links.
2. Read `problem.md` (requirements as written), then `spec.md` (exact rules; "Round 6 Details" is at the end).
3. Read `file_analyzer.py`; `main` holds the Round 6 change.
4. Read the R24-R28 classes at the end of `tests/test_file_analyzer.py`.
5. Read `docs/decisions/0008-summary-only-flag.md` and `README.md` ("Show only the summary").
6. Try it, for example:
   - `python file_analyzer.py --summary-only problem.md spec.md`
   - `python file_analyzer.py problem.md spec.md --summary-only`
   - `python file_analyzer.py --summary-only` (usage error, exit code 2)
7. See the Round 6 history with `git log --oneline 8cc789b~1..HEAD`.

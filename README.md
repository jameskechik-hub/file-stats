# File Statistics Analyzer

A command-line program that counts the lines, words, and characters in one or more text files, or in every `.txt` file in a directory, and finds the longest word in each.

## Requirements

- Python 3 (tested with 3.13 on Windows)
- No third-party packages, so there is nothing to install

## Run the program

From the project root:

```
python file_analyzer.py [--summary-only] <file_path> [<file_path> ...]
```

Each path can be a file or a directory. `--summary-only` is optional (see [Show only the summary](#show-only-the-summary)).

For example:

```
python file_analyzer.py problem.md
python file_analyzer.py "C:\My Files\notes.txt"
python file_analyzer.py notes.txt draft.txt
```

The output looks like this:

```text
File:       notes.txt
Lines:      12
Words:      85
Characters: 472
Longest:    extraordinary (13 characters)
```

With two or more paths, each file gets its own block, followed by combined totals for the files that were analyzed successfully:

```text
File:       notes.txt
Lines:      12
Words:      85
Characters: 472
Longest:    extraordinary (13 characters)

File:       draft.txt
Lines:      3
Words:      20
Characters: 110
Longest:    beginning (9 characters)

Total (2 files)
Lines:      15
Words:      105
Characters: 582
Succeeded:  2
Failed:     0
```

If a file cannot be analyzed, its error is shown and the program continues with the next file. The summary at the end shows how many files were analyzed successfully (`Succeeded:`) and how many failed (`Failed:`). A path given twice is analyzed twice and counted twice. With a single path there is no summary.

## Analyze a directory

Give a directory instead of a file to analyze every `.txt` file directly inside it:

```
python file_analyzer.py notes
python file_analyzer.py "C:\My Files\notes"
python file_analyzer.py intro.txt notes chapters
```

- Only regular files whose names end in `.txt` are analyzed. Upper and lower case do not matter, so `READ.TXT` is included.
- Other files (`readme.md`, `notes.txt.bak`) and subdirectories are ignored and are not counted. Subdirectories are never searched.
- Files are processed in alphabetical order by name, ignoring case (`A.txt`, `apple.txt`, `b.txt`, `Cat.txt`). Numbers are compared character by character, so `10.txt` comes before `2.txt`.
- The `File:` line shows the directory as you typed it, joined with the file name (`notes\A.txt` on Windows, `notes/A.txt` on Linux and macOS).
- Directories and files can be mixed. Each directory is replaced, in place, by its `.txt` files.
- A directory always gets the summary, even with only one `.txt` file. An empty directory prints a summary of zeros and exits with code 0.
- If a `.txt` file cannot be read, its error is shown, it is counted in `Failed:`, and the program continues. A directory that cannot be listed is reported and counted as one failure.

For example, if `notes` holds `A.txt`, `b.txt`, a file `bad.txt` that is not UTF-8, `readme.md`, and a subdirectory `old`, then on Windows `python file_analyzer.py notes` prints:

```text
File:       notes\A.txt
Lines:      2
Words:      3
Characters: 14
Longest:    three (5 characters)

File:       notes\b.txt
Lines:      1
Words:      1
Characters: 4
Longest:    four (4 characters)

Total (2 files)
Lines:      3
Words:      4
Characters: 18
Succeeded:  2
Failed:     1
```

and shows this error, then exits with code 1:

```text
Error: 'notes\bad.txt' is not valid UTF-8. Only UTF-8 text is supported.
```

## Show only the summary

Add `--summary-only` to print only the combined totals and file counts, without a block for each file:

```
python file_analyzer.py --summary-only notes.txt draft.txt
python file_analyzer.py --summary-only notes
python file_analyzer.py intro.txt notes chapters --summary-only
```

For example, `python file_analyzer.py --summary-only a.txt missing.txt b.txt` prints:

```text
Total (2 files)
Lines:      3
Words:      4
Characters: 18
Succeeded:  2
Failed:     1
```

and shows this error, then exits with code 1:

```text
Error: 'missing.txt' was not found. Check the path and try again.
```

- The summary is the same one shown at the end of the normal output. Only the file blocks are left out.
- The summary is always shown with `--summary-only`, even for a single file (`Total (1 file)`).
- It works with files, directories, and any mix of them. An empty directory gives a summary of zeros.
- The flag can go before, after, or between the paths. Abbreviations such as `--summary` are not accepted.
- Errors are still shown, and the exit codes are the same as without the flag.
- `--summary-only` with no paths shows `error: --summary-only requires at least one file or directory path.` and exits with code 2.
- Without `--summary-only`, the output is exactly as before.

## Other options

Show usage with `python file_analyzer.py --help`. If a file name starts with a dash, put `./` before it: `python file_analyzer.py "./-notes.txt"`. This also works for a file named `--summary-only`.

## How counting works

- **Lines:** every line counts, including blank lines and a last line with no line break.
- **Words:** any text separated by whitespace is a word, including `--`.
- **Characters:** spaces, tabs, and line breaks count. A Windows line break counts as one character, so the total can be smaller than the file size.
- **Longest word:** uses the same words as the word count, so punctuation is part of the word (`end.` has 4 characters). If several words are equally long, the first one in the file is shown. A file with no words shows `N/A (0 characters)`. The totals do not include a longest word.

See [spec.md](spec.md) for the exact rules.

## Errors

Error messages are written to stderr.

| Exit code | Meaning |
|---|---|
| 0 | Every file was analyzed (including an empty directory) |
| 1 | At least one file could not be analyzed, a directory could not be listed, or the results could not be written |
| 2 | The command-line arguments were wrong (including `--summary-only` with no paths) |

Only UTF-8 text is supported. In Windows PowerShell 5.1, `>` creates UTF-16 files by default, so create test files like this instead:

```powershell
Set-Content notes.txt "hello world" -Encoding utf8
```

## Run the tests

From the project root:

```
python -m unittest
```

Add `-v` to list each test. The tests are in `tests/test_file_analyzer.py`, with one class for each requirement:

| Requirement | Test class |
|---|---|
| R1: Accept a file path | `TestR1Input` |
| R2: Count lines | `TestR2Lines` |
| R3: Count words | `TestR3Words` |
| R4: Count characters | `TestR4Characters` |
| R5: Display results | `TestR5Output` |
| R6: Report errors | `TestR6Errors` |
| R9: Accept multiple paths | `TestR9MultiplePaths` |
| R10: Separate statistics per file | `TestR10SeparateStatistics` |
| R11 (revised in Round 4): Continue after a file error, report each error, and count successes and failures | `TestR11ContinueAfterErrors` |
| R12: Combined totals | `TestR12CombinedTotals` |
| R13: Find the longest word | `TestR13LongestWord` |
| R14: Display the longest word and its length | `TestR14LongestWordDisplay` |
| R15: First word wins a tie | `TestR15LongestWordTies` |
| R16: N/A when a file has no words | `TestR16NoWords` |
| R17: Number of successful files in the summary | `TestR17SucceededCount` |
| R18: Number of failed files in the summary | `TestR18FailedCount` |
| R19: Accept a directory and analyze its `.txt` files | `TestR19DirectoryInput` |
| R20: No subdirectories, alphabetical order | `TestR20DirectoryOrder` |
| R21: Statistics for each file in the directory | `TestR21DirectoryFileStatistics` |
| R22: Combined totals and counts for a directory | `TestR22DirectoryTotals` |
| R23: Report unreadable files and continue | `TestR23DirectoryErrors` |
| R24: Accept the optional `--summary-only` flag | `TestR24SummaryOnlyFlag` |
| R25: Show only the combined statistics | `TestR25OnlyCombinedStatistics` |
| R26: Unchanged output without the flag | `TestR26OutputWithoutFlag` |
| R27: Works with files, directories, and mixes | `TestR27SummaryOnlyWithAllPathKinds` |
| R28: Error when the flag has no paths | `TestR28SummaryOnlyWithoutPaths` |

One test, `test_symbolic_link_to_a_file_is_included_and_broken_link_skipped`, is skipped when the system does not allow creating symbolic links (for example, Windows without Developer Mode or administrator rights).

## Design decisions

- [0001: Counting rules](docs/decisions/0001-counting-rules.md)
- [0002: UTF-8 only](docs/decisions/0002-utf8-only.md)
- [0003: Continue after file errors](docs/decisions/0003-continue-after-file-errors.md)
- [0004: Multi-file output layout](docs/decisions/0004-multi-file-output-layout.md)
- [0005: Longest word rules](docs/decisions/0005-longest-word-rules.md)
- [0006: Success and failure counts](docs/decisions/0006-success-and-failure-counts.md)
- [0007: Directory analysis](docs/decisions/0007-directory-analysis.md)
- [0008: Summary-only flag](docs/decisions/0008-summary-only-flag.md)

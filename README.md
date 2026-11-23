# File Statistics Analyzer

A command-line program that counts the lines, words, and characters in one or more text files.

## Requirements

- Python 3 (tested with 3.13 on Windows)
- No third-party packages, so there is nothing to install

## Run the program

From the project root:

```
python file_analyzer.py <file_path> [<file_path> ...]
```

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
```

With two or more paths, each file gets its own block, followed by combined totals for the files that were analyzed successfully:

```text
File:       notes.txt
Lines:      12
Words:      85
Characters: 472

File:       draft.txt
Lines:      3
Words:      20
Characters: 110

Total (2 files)
Lines:      15
Words:      105
Characters: 582
```

If a file cannot be analyzed, its error is shown and the program continues with the next file. A path given twice is analyzed twice.

Show usage with `python file_analyzer.py --help`. If a file name starts with a dash, put `./` before it: `python file_analyzer.py "./-notes.txt"`.

## How counting works

- **Lines:** every line counts, including blank lines and a last line with no line break.
- **Words:** any text separated by whitespace is a word, including `--`.
- **Characters:** spaces, tabs, and line breaks count. A Windows line break counts as one character, so the total can be smaller than the file size.

See [spec.md](spec.md) for the exact rules.

## Errors

Error messages are written to stderr.

| Exit code | Meaning |
|---|---|
| 0 | Every file was analyzed |
| 1 | At least one file could not be analyzed, or the results could not be written |
| 2 | The command-line arguments were wrong |

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
| R11: Continue after a file error | `TestR11ContinueAfterErrors` |
| R12: Combined totals | `TestR12CombinedTotals` |

## Design decisions

- [0001: Counting rules](docs/decisions/0001-counting-rules.md)
- [0002: UTF-8 only](docs/decisions/0002-utf8-only.md)
- [0003: Continue after file errors](docs/decisions/0003-continue-after-file-errors.md)
- [0004: Multi-file output layout](docs/decisions/0004-multi-file-output-layout.md)

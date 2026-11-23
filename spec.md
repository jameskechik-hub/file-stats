\# File Statistics Analyzer Specification



\## Purpose

Build a Python command-line application that analyzes text files and displays useful statistics.



\## Requirements

1: Accept a text file path as a command-line argument.

2: Count the number of lines in the file.

3: Count the number of words in the file.

4: Count the number of characters in the file.

5: Display the statistics clearly in the terminal.

6: The program must display a helpful error message if anything goes wrong.

9: Accept multiple text file paths in a single command.

10: Display separate statistics for each successfully analyzed file.

11 (Revised in Round 4): When analyzing multiple files, continue after an individual file fails, display an error for each failed file, and report the number of successfully analyzed and failed files in the final summary.

12: Display combined totals for lines, words, and characters across all successfully analyzed files.

13: Identify the longest word in each successfully analyzed text file.

14: Display the longest word and its character length alongside the existing file statistics.

15: If multiple words share the maximum length, report the first one encountered.

16: If a file contains no words, display "N/A" for its longest word and 0 for its length.

17: The final summary must display the total number of successfully analyzed files.

18: The final summary must display the total number of files that failed analysis.



\##  Design

\- Interface: Command-line

\- Program Name: file\_analyzer.py

* Have a testing framework and a way to easily run all tests with one command



\## Constraints

\- Run locally without paid services.

\- Keep the application simple.



## Round 1 Details

R1-R6 refer to requirements 1-6 above.

### R1: Input

- Usage: `python file_analyzer.py <file_path>`
- Relative paths, absolute paths, and quoted paths containing spaces work.
- Changed in Round 2: R9 replaces the Round 1 rule that exactly one path is accepted.
- `-h` and `--help` show usage and exit with code 0.

### R2: Lines

- A line is text ended by a line break, plus any final text without a line break.
- Line breaks are `\r\n`, `\n`, or a lone `\r`. No other character ends a line.
- Blank lines count. An empty file has 0 lines.

### R3: Words

- A word is any run of non-whitespace characters, using the whitespace rules of Python's `str.split()`.
- Punctuation-only pieces such as `--` count as words.

### R4: Characters

- A character is a decoded Unicode code point, not a byte.
- Spaces and tabs count. Each line break, including `\r\n`, counts as 1 character.
- A byte order mark (BOM) at the start of the file is not counted.

### Examples for R2-R4

| File content | Lines | Words | Characters |
|---|---|---|---|
| (empty) | 0 | 0 | 0 |
| `\n` | 1 | 0 | 1 |
| `a\nb` | 2 | 2 | 3 |
| `a\nb\n` | 2 | 2 | 4 |
| `hi\r\n` | 1 | 1 | 3 |
| `don't stop -- well-known` | 1 | 4 | 24 |

### R5: Output

Results go to stdout in this format, showing the path as the user typed it:

```text
File:       notes.txt
Lines:      12
Words:      85
Characters: 472
```

Changed in Round 3: R14 adds a `Longest:` line after `Characters:`.

### R6: Errors

- Supported text files are UTF-8 (including ASCII), with or without a BOM.
- Errors go to stderr with no traceback and no statistics on stdout.
- An empty file is valid and is not an error.

| Situation | Message explains | Exit code |
|---|---|---|
| Success | (results are displayed) | 0 |
| Missing arguments or an unknown option | Correct usage | 2 |
| File does not exist | File was not found | 1 |
| Path is a directory | A file is required | 1 |
| File cannot be read due to permissions | Permission was denied | 1 |
| File is not valid UTF-8 | Only UTF-8 text is supported | 1 |
| File contains a NUL byte | File appears to be binary or not UTF-8 | 1 |
| Any other read failure | File could not be read, and why | 1 |

With one path, these rules apply exactly as written. With several paths, R11 decides what happens when a file fails.

### Testing

- Framework: `unittest`
- Run all tests from the project root with `python -m unittest`.
- Every requirement R1-R6, R9-R12, R13-R16, and R17-R18 has at least one test.



## Round 2 Details

R9-R12 refer to requirements 9-12 above. Requirement numbers 7 and 8 are not used.

### R9: Multiple paths

- Usage: `python file_analyzer.py <file_path> [<file_path> ...]`
- One or more paths are accepted. With no paths, the program shows usage and exits with code 2.
- Files are processed in the order given.
- A path given more than once is analyzed each time and is counted in the totals each time.

### R10: Separate statistics

- Each successfully analyzed file gets its own block in the R5 format.
- Blocks are separated by one blank line.
- With one path, the output is exactly the Round 1 output. (Round 3 adds the R14 `Longest:` line to every block.)

### R11: Errors while processing several files

Revised in Round 4: R11 now also requires the final summary to report how many files succeeded and how many failed. See "Round 4 Details" below.

- A file that cannot be analyzed gets an error message on stderr, using the same messages as R6, and no block on stdout.
- The program then continues with the next file.
- Exit codes:

| Situation | Exit code |
|---|---|
| Every file was analyzed | 0 |
| At least one file could not be analyzed | 1 |
| Missing arguments or an unknown option (nothing is analyzed) | 2 |
| Results could not be written to stdout (processing stops) | 1 |

### R12: Combined totals

- Shown only when two or more paths are given, after all file blocks and separated by one blank line.
- Totals add up the lines, words, and characters of the successfully analyzed files only.
- The header gives the number of successfully analyzed files, as `1 file` or `N files`.
- If no file was analyzed successfully, the totals are still shown, with `0 files` and zeros.
- Changed in Round 4: R17 and R18 add `Succeeded:` and `Failed:` lines to the end of this block.

Example with `python file_analyzer.py a.txt missing.txt b.txt`:

```text
File:       a.txt
Lines:      2
Words:      5
Characters: 20

File:       b.txt
Lines:      3
Words:      4
Characters: 18

Total (2 files)
Lines:      5
Words:      9
Characters: 38
```

and on stderr:

```text
Error: 'missing.txt' was not found. Check the path and try again.
```

The exit code is 1.

Changed in Round 3: each file block in this example also gets the R14 `Longest:` line. The totals block does not change. See the Round 3 example below.

Changed in Round 4: the totals block also gets `Succeeded:` and `Failed:` lines. See the Round 4 example below.



## Round 3 Details

R13-R16 refer to requirements 13-16 above.

### R13: Longest word

- A word is defined exactly as in R3: any run of non-whitespace characters, using the whitespace rules of Python's `str.split()`. Punctuation stays part of the word, so `end.` is a 4-character word and `--` is a word.
- The longest word is found for each successfully analyzed file only. A file that fails (R6, R11) has no longest word.
- The longest word is shown exactly as it appears in the file, with its original letter case.

### R14: Display

- Each file block gets one more line, after `Characters:`, in the same aligned format:

```text
File:       notes.txt
Lines:      12
Words:      85
Characters: 472
Longest:    extraordinary (13 characters)
```

- The length is the number of characters in the word, counted as in R4: decoded Unicode code points. `café` has length 4, an emoji has length 1, and `e` followed by a combining accent has length 2.
- A length of 1 is shown as `(1 character)`. Every other length uses `characters`.
- The R12 totals block does not show a longest word. It is unchanged from Round 2.

### R15: Ties

- If several words share the maximum length, the first one in the file is shown. "First" means earliest in the file, reading lines from top to bottom and words from left to right.
- A later word that is equal in length does not replace the first one, even if it is a different word or has different letter case.

### R16: No words

- If a file has no words (it is empty or contains only whitespace), the line is:

```text
Longest:    N/A (0 characters)
```

- `N/A` here is not a word from the file. A file that really contains the word `N/A` shows `N/A (3 characters)`.

### Examples for R13-R16

| File content | Longest line |
|---|---|
| (empty) | `Longest:    N/A (0 characters)` |
| ` \n\t\r\n` | `Longest:    N/A (0 characters)` |
| `a` | `Longest:    a (1 character)` |
| `cat dog bird` | `Longest:    bird (4 characters)` |
| `cat dog ant` | `Longest:    cat (3 characters)` |
| `one\nthree\nseven` | `Longest:    three (5 characters)` |
| `don't stop -- well-known` | `Longest:    well-known (10 characters)` |
| `see the end.` | `Longest:    end. (4 characters)` |

Example with `python file_analyzer.py a.txt missing.txt b.txt`, where `a.txt` contains `one two\nthree\n` and `b.txt` contains `four`:

```text
File:       a.txt
Lines:      2
Words:      3
Characters: 14
Longest:    three (5 characters)

File:       b.txt
Lines:      1
Words:      1
Characters: 4
Longest:    four (4 characters)

Total (2 files)
Lines:      3
Words:      4
Characters: 18
```

The error for `missing.txt` goes to stderr as in Round 2, and the exit code is 1.

Changed in Round 4: the totals block in this example also ends with `Succeeded:  2` and `Failed:     1`. See the Round 4 example below.



## Round 4 Details

Round 4 revises R11 and adds R17-R18. All other requirements are unchanged.

### R11 (revised): Continue, report each error, and count the results

- What did not change: with several paths, a file that fails gets its R6 error message on stderr and no block on stdout, and the program continues with the next file. The exit codes in the Round 2 R11 table do not change.
- What is new: the final summary reports how many files were analyzed successfully (R17) and how many failed (R18).
- A file "fails" when it produces any R6 file error: not found, a directory, permission denied, not valid UTF-8, contains a NUL byte, or any other read failure.
- The "final summary" is the R12 totals block. It is shown only when two or more paths are given. With one path, the output is exactly as in Round 3, with no summary.
- If the results cannot be written to stdout, processing stops at once with exit code 1, as in Round 2, and no summary is shown.
- Usage errors (no paths, unknown option) analyze nothing, show no summary, and exit with code 2, as before.

### R17: Successful file count

- The totals block gets a `Succeeded:` line after `Characters:`, in the same aligned format.
- The number is the count of successfully analyzed files. It is the same number as in the `Total (N files)` header.

### R18: Failed file count

- The totals block gets a `Failed:` line after `Succeeded:`.
- The number is the count of files that failed analysis.
- The line is always shown, including `Failed:     0` when every file succeeded.
- `Succeeded` plus `Failed` always equals the number of paths given. A path given more than once is counted each time, as in R9.

### Summary format

```text
Total (2 files)
Lines:      3
Words:      4
Characters: 18
Succeeded:  2
Failed:     1
```

- The header and the `Lines:`, `Words:`, and `Characters:` lines are unchanged from R12.
- The counts are plain numbers, with no `file`/`files` noun, so there is no singular form to choose.
- File blocks (R5, R10, R14) are unchanged.

### Examples for R11, R17, and R18

| Command | `Succeeded:` | `Failed:` | Exit code |
|---|---|---|---|
| `a.txt b.txt` | 2 | 0 | 0 |
| `a.txt missing.txt b.txt` | 2 | 1 | 1 |
| `missing1.txt missing2.txt` | 0 | 2 | 1 |
| `a.txt a.txt missing.txt missing.txt` | 2 | 2 | 1 |
| `a.txt` (one path) | no summary | no summary | 0 |
| `missing.txt` (one path) | no summary | no summary | 1 |

Example with `python file_analyzer.py a.txt missing.txt b.txt`, where `a.txt` contains `one two\nthree\n` and `b.txt` contains `four`:

```text
File:       a.txt
Lines:      2
Words:      3
Characters: 14
Longest:    three (5 characters)

File:       b.txt
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

and on stderr:

```text
Error: 'missing.txt' was not found. Check the path and try again.
```

The exit code is 1.

When every file fails, for example `python file_analyzer.py missing1.txt missing2.txt`:

```text
Total (0 files)
Lines:      0
Words:      0
Characters: 0
Succeeded:  0
Failed:     2
```

with two error lines on stderr and exit code 1.

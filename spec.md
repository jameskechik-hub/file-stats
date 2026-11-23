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

11: If one file cannot be read, report the error and continue processing the remaining files.

12: Display combined totals for lines, words, and characters across all successfully analyzed files.



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
- Every requirement R1-R6 and R9-R12 has at least one test.



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
- With one path, the output is exactly the Round 1 output.

### R11: Errors while processing several files

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

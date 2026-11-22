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
- Exactly one path is accepted. Relative paths, absolute paths, and quoted paths containing spaces work.
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
| Missing or extra arguments | Correct usage | 2 |
| File does not exist | File was not found | 1 |
| Path is a directory | A file is required | 1 |
| File cannot be read due to permissions | Permission was denied | 1 |
| File is not valid UTF-8 | Only UTF-8 text is supported | 1 |
| File contains a NUL byte | File appears to be binary or not UTF-8 | 1 |
| Any other read failure | File could not be read, and why | 1 |

### Testing

- Framework: `unittest`
- Run all tests from the project root with `python -m unittest`.
- Every requirement R1-R6 has at least one test.

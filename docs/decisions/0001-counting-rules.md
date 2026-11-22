# 0001: Count normalized text, one line at a time

- Status: Accepted
- Date: 2026-11-22
- Requirements: R2, R3, R4

## Y-statement

**In the context of** counting lines, words, and characters in text files that may be large and may come from Windows, macOS, or Linux,

**facing** different line-ending styles and files that may lack a final newline,

**we decided for** reading the file one line at a time in Python's text mode, which turns `\r\n` and `\r` into `\n`, and counting each line it returns,

**and neglected** counting newline bytes like `wc -l`, counting raw characters, and calling `read().splitlines()` on the whole file,

**to achieve** the same counts on every operating system, a line count that matches what users see, and low memory use,

**accepting that** character counts differ from file size, line counts can differ from `wc -l`, and a very long single line is still loaded into memory at once.

## Why not `splitlines()`?

`str.splitlines()` also splits on characters such as form feed and U+2028. The specification says only `\r\n`, `\n`, and `\r` end a line.

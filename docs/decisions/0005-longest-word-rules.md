# 0005: Find the longest word with the R3 word rule and show it on one line

- Status: Accepted
- Date: 2026-11-22
- Requirements: R3, R4, R13, R14, R15, R16

## Y-statement

**In the context of** reporting the longest word in each analyzed file alongside its line, word, and character counts,

**facing** the questions of what a "word" is, how its length is measured, where it appears in the output, and what to show for a file with no words or several equally long words,

**we decided for** using exactly the words that R3 already counts (runs of non-whitespace from `str.split()`, punctuation included), measuring length in code points as R4 does, keeping the first word that is strictly longer than all before it, and adding one aligned line `Longest:    <word> (<n> characters)` to each file block, with `N/A (0 characters)` when there are no words and no longest word in the totals block,

**and neglected** stripping punctuation from the edges of words, counting only letters and digits, measuring visible characters (grapheme clusters), a two-line `Longest word:`/`Length:` layout that would widen every label, and a longest word across all files in the totals block,

**to achieve** one consistent definition of "word" for both the count and the longest word, a length that agrees with the character count, Round 1 and Round 2 lines that stay exactly as they were, and simple code that finds the word in the same single pass over the file,

**accepting that** punctuation can make a word look longer than expected (`end.` has length 4 and a Markdown link can be the "longest word"), and that an accented letter written as a letter plus a combining mark counts as 2 characters.

## Notes

- The user chose the word rule, the one-line layout, code point lengths, and leaving the totals block unchanged before any code was written.
- A length of 1 is shown as `(1 character)`, matching the singular `1 file` in the totals header.
- `FileStats.longest_word` is an empty string when a file has no words. `N/A` is produced only when formatting, so a file that really contains the word `N/A` is still shown correctly as `N/A (3 characters)`.

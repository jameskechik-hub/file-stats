# 0002: Accept only UTF-8 text

- Status: Accepted
- Date: 2026-11-22
- Requirements: R4, R6

## Y-statement

**In the context of** analyzing files that are supposed to contain text,

**facing** the fact that a file's encoding cannot be detected reliably and that a wrong guess gives wrong counts,

**we decided for** accepting only UTF-8, with or without a BOM, and rejecting files that contain NUL bytes,

**and neglected** UTF-16 support, encoding detection, and replacing invalid bytes,

**to achieve** trustworthy counts, clear errors, and simple code with no third-party modules,

**accepting that** users must convert other files to UTF-8 first, including the UTF-16 files that `>` creates by default in Windows PowerShell 5.1.

\# Problem



Users sometimes need to understand the contents of text files quickly. Manually counting words, lines, and/or characters is tedious, especially when working with larger files. A simple command-line tool could make this process faster and more convenient.



\# Initial requirements



1: The program must accept a text file path as a command-line argument.

2: The program must count the total number of lines in the file.

3: The program must count the total number of words in the file.

4: The program must count the total number of characters in the file.

5: The program must display the results clearly in the terminal.

6: The program must display a helpful error message if anything goes wrong.





\## Round 2: Multiple File Analysis



9: The program must accept multiple text file paths in a single command.

10: The program must display separate statistics for each successfully analyzed file.

11 (Revised in Round 4): When analyzing multiple files, the program must continue after an individual file fails, display an error for each failed file, and report the number of successfully analyzed and failed files in the final summary.

12: The program must display combined totals for lines, words, and characters across all successfully analyzed files.





\## Round 3: Longest Word Analysis



13: The program must identify the longest word in each successfully analyzed text file.

14: The program must display the longest word and its character length alongside the existing file statistics.

15: If multiple words share the maximum length, the program must report the first one encountered.

16: If a file contains no words, the program must display "N/A" for its longest word and 0 for its length.





\## Round 4: Error Reporting Improvements



This round revises R11 from Round 2 to require explicit success and failure counts in the final summary.



17: The final summary must display the total number of successfully analyzed files.

18: The final summary must display the total number of files that failed analysis.





\## Round 5: Directory Analysis



19: The program must accept a directory path as a command-line argument and analyze all regular files ending in .txt directly inside that directory.



20: Directory analysis must not search subdirectories. Files must be processed in alphabetical order by filename.



21: The program must display individual statistics for every successfully analyzed .txt file in the directory, following the existing output format.



22: The program must display combined totals for all successfully analyzed files, including the successful and failed file counts introduced in Round 4.



23: If an individual .txt file cannot be read, the program must report the error and continue analyzing the remaining eligible files.




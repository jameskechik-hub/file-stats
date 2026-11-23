"""Automated tests, with one test class for each requirement (R1-R6, R9-R23)."""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import file_analyzer

PROGRAM = Path(file_analyzer.__file__).resolve()


class AnalyzerTestCase(unittest.TestCase):
    """Give each test an empty temporary directory and some helpers."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)

    def write(self, content, name="notes.txt"):
        # Bytes are written so that line endings are identical on every system.
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def analyze(self, content):
        return file_analyzer.analyze_file(self.write(content))

    def run_program(self, *args, env=None):
        return subprocess.run(
            [sys.executable, str(PROGRAM), *map(str, args)],
            cwd=self.directory,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )


class TestR1Input(AnalyzerTestCase):
    def test_accepts_relative_path(self):
        self.write(b"hello", "folder/notes.txt")
        result = self.run_program("folder/notes.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Words:      1", result.stdout)

    def test_accepts_absolute_path(self):
        result = self.run_program(self.write(b"hello").resolve())
        self.assertEqual(result.returncode, 0)
        self.assertIn("Words:      1", result.stdout)

    def test_accepts_path_with_spaces(self):
        self.write(b"hello", "my folder/my notes.txt")
        result = self.run_program("my folder/my notes.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Words:      1", result.stdout)

    def test_accepts_non_ascii_path(self):
        self.write(b"hello", "caf\u00e9.txt")
        result = self.run_program("caf\u00e9.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Words:      1", result.stdout)

    def test_help_shows_usage(self):
        for option in ("-h", "--help"):
            with self.subTest(option=option):
                result = self.run_program(option)
                self.assertEqual(result.returncode, 0)
                self.assertIn("usage: file_analyzer.py", result.stdout)
                self.assertIn("file_path", result.stdout)


class TestR2Lines(AnalyzerTestCase):
    def assert_lines(self, content, expected):
        self.assertEqual(self.analyze(content).lines, expected)

    def test_empty_file_has_no_lines(self):
        self.assert_lines(b"", 0)

    def test_single_newline_is_one_line(self):
        self.assert_lines(b"\n", 1)

    def test_last_line_without_newline_counts(self):
        self.assert_lines(b"a\nb", 2)

    def test_final_newline_does_not_add_a_line(self):
        self.assert_lines(b"a\nb\n", 2)

    def test_blank_lines_count(self):
        self.assert_lines(b"a\n\n\nb\n\n", 5)

    def test_windows_line_endings(self):
        self.assert_lines(b"a\r\nb\r\n", 2)

    def test_lone_carriage_returns(self):
        self.assert_lines(b"a\rb\r", 2)

    def test_mixed_line_endings(self):
        self.assert_lines(b"a\r\nb\nc\rd", 4)

    def test_other_separators_do_not_end_a_line(self):
        for separator in "\v\f\x1c\x1d\x1e\x85\u2028\u2029":
            with self.subTest(separator=separator):
                self.assert_lines(f"a{separator}b".encode(), 1)

    def test_large_file(self):
        self.assert_lines(b"line\r\n" * 100_000, 100_000)


class TestR3Words(AnalyzerTestCase):
    def assert_words(self, content, expected):
        self.assertEqual(self.analyze(content).words, expected)

    def test_empty_file_has_no_words(self):
        self.assert_words(b"", 0)

    def test_only_whitespace_has_no_words(self):
        self.assert_words(b" \t\n  \r\n", 0)

    def test_repeated_whitespace_separates_once(self):
        self.assert_words(b"  one   two\t\tthree  ", 3)

    def test_line_breaks_separate_words(self):
        self.assert_words(b"one\ntwo\r\nthree\rfour", 4)

    def test_punctuation_follows_whitespace_rule(self):
        self.assert_words(b"don't stop -- well-known", 4)

    def test_unicode_whitespace_separates_words(self):
        self.assert_words("one\u00a0two\u2003three".encode(), 3)

    def test_bom_alone_is_not_a_word(self):
        self.assert_words(b"\xef\xbb\xbf", 0)

    def test_large_file(self):
        self.assert_words(b"two words\n" * 100_000, 200_000)


class TestR4Characters(AnalyzerTestCase):
    def assert_characters(self, content, expected):
        self.assertEqual(self.analyze(content).characters, expected)

    def test_empty_file_has_no_characters(self):
        self.assert_characters(b"", 0)

    def test_spec_examples(self):
        examples = (
            (b"\n", 1),
            (b"a\nb", 3),
            (b"a\nb\n", 4),
            (b"hi\r\n", 3),
            (b"don't stop -- well-known", 24),
        )
        for content, expected in examples:
            with self.subTest(content=content):
                self.assert_characters(content, expected)

    def test_spaces_and_tabs_count(self):
        self.assert_characters(b" a\tb ", 5)

    def test_each_style_of_line_break_is_one_character(self):
        self.assert_characters(b"a\r\nb\nc\rd", 7)

    def test_counts_code_points_instead_of_bytes(self):
        self.assert_characters("caf\u00e9 \U0001f600".encode(), 6)

    def test_combining_mark_is_its_own_code_point(self):
        self.assert_characters("e\u0301".encode(), 2)

    def test_leading_bom_is_not_counted(self):
        self.assert_characters(b"\xef\xbb\xbfhi", 2)

    def test_later_bom_character_is_counted(self):
        self.assert_characters("a\ufeffb".encode(), 3)

    def test_large_file(self):
        self.assert_characters(b"line\r\n" * 100_000, 500_000)

    def test_long_single_line(self):
        self.assert_characters(b"x" * 1_000_000, 1_000_000)


class TestR5Output(AnalyzerTestCase):
    def test_exact_report(self):
        self.write(b"one two\r\nthree\r\n")
        result = self.run_program("notes.txt")
        self.assertEqual(
            result.stdout,
            "File:       notes.txt\n"
            "Lines:      2\n"
            "Words:      3\n"
            "Characters: 14\n"
            "Longest:    three (5 characters)\n",
        )
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)

    def test_empty_file_shows_zeros(self):
        self.write(b"")
        result = self.run_program("notes.txt")
        self.assertEqual(
            result.stdout,
            "File:       notes.txt\n"
            "Lines:      0\n"
            "Words:      0\n"
            "Characters: 0\n"
            "Longest:    N/A (0 characters)\n",
        )
        self.assertEqual(result.returncode, 0)

    def test_path_is_shown_as_typed(self):
        self.write(b"hello")
        result = self.run_program("./notes.txt")
        self.assertIn("File:       ./notes.txt\n", result.stdout)

    def test_unprintable_file_name_does_not_crash(self):
        self.write(b"hello", "\u65e5.txt")
        env = {**os.environ, "PYTHONIOENCODING": "ascii", "PYTHONUTF8": "1"}
        result = self.run_program("\u65e5.txt", env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("File:       \\u65e5.txt\n", result.stdout)


class TestR6Errors(AnalyzerTestCase):
    def assert_error(self, result, message, code=1):
        self.assertEqual(result.returncode, code)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")

    def assert_open_failure(self, opener, message):
        """Simulate failures that cannot be created reliably on every system."""
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("builtins.open", opener):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = file_analyzer.main(["notes.txt"])
        self.assertEqual(code, 1)
        self.assertIn(message, stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")

    def test_missing_argument(self):
        result = self.run_program()
        self.assert_error(result, "usage: file_analyzer.py", code=2)
        self.assertIn("required: file_path", result.stderr)

    def test_unknown_option(self):
        result = self.run_program("--unknown", "notes.txt")
        self.assert_error(result, "usage: file_analyzer.py", code=2)

    def test_missing_file(self):
        self.assert_error(self.run_program("missing.txt"), "was not found")

    def test_empty_path(self):
        self.assert_error(self.run_program(""), "was not found")

    def test_directory_is_no_longer_an_error(self):
        # Changed in Round 5: R19 replaces the Round 1 "path is a directory" error.
        result = self.run_program(".")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_analyze_file_still_rejects_a_directory(self):
        # main() expands directories (R19); analyze_file() itself only reads files.
        with self.assertRaisesRegex(file_analyzer.AnalysisError, "is a directory"):
            file_analyzer.analyze_file(str(self.directory))

    def test_invalid_utf8(self):
        self.write(b"caf\xe9")
        self.assert_error(self.run_program("notes.txt"), "Only UTF-8 text is supported")

    def test_utf16_with_bom(self):
        self.write("hello".encode("utf-16"))
        self.assert_error(self.run_program("notes.txt"), "Only UTF-8 text is supported")

    def test_utf16_without_bom(self):
        self.write("hello".encode("utf-16-le"))
        self.assert_error(self.run_program("notes.txt"), "binary or not UTF-8")

    def test_nul_byte(self):
        self.write(b"ab\x00cd")
        self.assert_error(self.run_program("notes.txt"), "binary or not UTF-8")

    def test_problem_late_in_file_prints_no_statistics(self):
        self.write(b"good line\n" * 10_000 + b"\xff")
        self.assert_error(self.run_program("notes.txt"), "Only UTF-8 text is supported")

    def test_permission_denied(self):
        opener = mock.Mock(side_effect=PermissionError(13, "Permission denied"))
        self.assert_open_failure(opener, "Permission denied when reading 'notes.txt'")

    def test_other_open_failure_explains_why(self):
        opener = mock.Mock(side_effect=OSError(5, "Input/output error"))
        self.assert_open_failure(opener, "Input/output error")

    def test_failure_during_read_explains_why(self):
        opener = mock.MagicMock()
        file = opener.return_value.__enter__.return_value
        file.__iter__.side_effect = OSError("device disconnected")
        self.assert_open_failure(opener, "device disconnected")

    def test_out_of_memory(self):
        opener = mock.Mock(side_effect=MemoryError)
        self.assert_open_failure(opener, "not enough memory")

    def test_output_cannot_be_written(self):
        self.write(b"hello")
        read_end, write_end = os.pipe()
        os.close(read_end)  # With no reader, every write to the pipe fails.
        try:
            result = subprocess.run(
                [sys.executable, str(PROGRAM), "notes.txt"],
                cwd=self.directory,
                stdout=write_end,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        finally:
            os.close(write_end)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "Error: Could not write the results.\n")


def longest_line(word):
    """Return the R14 line for a longest word, or the R16 line when it is None."""
    if word is None:
        return "Longest:    N/A (0 characters)\n"
    noun = "character" if len(word) == 1 else "characters"
    return f"Longest:    {word} ({len(word)} {noun})\n"


def block(path, lines, words, characters, longest):
    """Return one file's report, as printed by the program."""
    return (
        f"File:       {path}\n"
        f"Lines:      {lines}\n"
        f"Words:      {words}\n"
        f"Characters: {characters}\n"
    ) + longest_line(longest)


def totals(header, lines, words, characters, succeeded, failed):
    """Return the final summary: R12 totals plus the R17 and R18 file counts."""
    return (
        f"Total ({header})\n"
        f"Lines:      {lines}\n"
        f"Words:      {words}\n"
        f"Characters: {characters}\n"
        f"Succeeded:  {succeeded}\n"
        f"Failed:     {failed}\n"
    )


def summary_counts(stdout):
    """Return the last two lines of the output, where R17 and R18 put the counts."""
    return stdout.splitlines()[-2:]


class MultiFileTestCase(AnalyzerTestCase):
    """Create two small files whose statistics are easy to check."""

    def setUp(self):
        super().setUp()
        self.write(b"one two\nthree\n", "a.txt")  # 2 lines, 3 words, 14 characters
        self.write(b"four", "b.txt")  # 1 line, 1 word, 4 characters


class TestR9MultiplePaths(MultiFileTestCase):
    def test_accepts_two_paths(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn(block("a.txt", 2, 3, 14, "three"), result.stdout)
        self.assertIn(block("b.txt", 1, 1, 4, "four"), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_accepts_many_paths_of_different_kinds(self):
        self.write(b"x y", "my folder/c d.txt")
        absolute = self.write(b"z", "e.txt").resolve()
        result = self.run_program("a.txt", "my folder/c d.txt", absolute, "./b.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("File:"), 4)
        self.assertIn(block("my folder/c d.txt", 1, 2, 3, "x"), result.stdout)
        self.assertIn(block(absolute, 1, 1, 1, "z"), result.stdout)

    def test_files_are_processed_in_the_order_given(self):
        result = self.run_program("b.txt", "a.txt")
        self.assertLess(result.stdout.index("b.txt"), result.stdout.index("a.txt"))

    def test_repeated_path_is_analyzed_each_time(self):
        result = self.run_program("a.txt", "a.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count(block("a.txt", 2, 3, 14, "three")), 2)

    def test_help_shows_several_paths(self):
        result = self.run_program("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("file_path [file_path ...]", result.stdout)

    def test_no_paths_shows_usage(self):
        result = self.run_program()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: file_analyzer.py", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unknown_option_analyzes_nothing(self):
        result = self.run_program("a.txt", "--unknown", "b.txt")
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: file_analyzer.py", result.stderr)
        self.assertEqual(result.stdout, "")


class TestR10SeparateStatistics(MultiFileTestCase):
    def test_exact_output_for_two_files(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertEqual(
            result.stdout,
            block("a.txt", 2, 3, 14, "three")
            + "\n"
            + block("b.txt", 1, 1, 4, "four")
            + "\n"
            + totals("2 files", 3, 4, 18, 2, 0),
        )

    def test_each_file_gets_its_own_counts(self):
        self.write(b"", "empty.txt")
        self.write(b"\r\n\r\n", "blank.txt")
        result = self.run_program("empty.txt", "blank.txt", "a.txt")
        self.assertIn(block("empty.txt", 0, 0, 0, None), result.stdout)
        self.assertIn(block("blank.txt", 2, 0, 2, None), result.stdout)
        self.assertIn(block("a.txt", 2, 3, 14, "three"), result.stdout)

    def test_single_path_output_is_unchanged(self):
        result = self.run_program("a.txt")
        self.assertEqual(result.stdout, block("a.txt", 2, 3, 14, "three"))
        self.assertEqual(result.returncode, 0)


class TestR11ContinueAfterErrors(MultiFileTestCase):
    """R11 (revised in Round 4): continue after a failure, show an error for
    each failed file, and report the success and failure counts in the summary."""

    def test_missing_file_in_the_middle(self):
        result = self.run_program("a.txt", "missing.txt", "b.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "Error: 'missing.txt' was not found. Check the path and try again.\n",
        )
        self.assertEqual(
            result.stdout,
            block("a.txt", 2, 3, 14, "three")
            + "\n"
            + block("b.txt", 1, 1, 4, "four")
            + "\n"
            + totals("2 files", 3, 4, 18, 2, 1),
        )

    def test_failure_first_or_last(self):
        for paths in (("missing.txt", "a.txt"), ("a.txt", "missing.txt")):
            with self.subTest(paths=paths):
                result = self.run_program(*paths)
                self.assertEqual(result.returncode, 1)
                self.assertIn("'missing.txt' was not found", result.stderr)
                self.assertEqual(
                    result.stdout,
                    block("a.txt", 2, 3, 14, "three")
                    + "\n"
                    + totals("1 file", 2, 3, 14, 1, 1),
                )

    def test_every_kind_of_error_is_reported_and_skipped(self):
        self.write(b"caf\xe9", "latin1.txt")
        self.write(b"ab\x00cd", "binary.txt")
        # Changed in Round 5: a directory is no longer an error (R19), so none is used here.
        result = self.run_program(
            "latin1.txt", "a.txt", "binary.txt", "missing.txt", "b.txt"
        )
        self.assertEqual(result.returncode, 1)
        errors = result.stderr.splitlines()
        self.assertEqual(len(errors), 3)
        self.assertIn("'latin1.txt' is not valid UTF-8", errors[0])
        self.assertIn("'binary.txt' appears to be binary", errors[1])
        self.assertIn("'missing.txt' was not found", errors[2])
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout.count("File:"), 2)
        self.assertNotIn("latin1.txt", result.stdout)
        self.assertEqual(
            summary_counts(result.stdout), ["Succeeded:  2", "Failed:     3"]
        )

    def test_each_failed_file_gets_its_own_error(self):
        result = self.run_program("missing1.txt", "a.txt", "missing2.txt", "b.txt")
        self.assertEqual(
            result.stderr,
            "Error: 'missing1.txt' was not found. Check the path and try again.\n"
            "Error: 'missing2.txt' was not found. Check the path and try again.\n",
        )
        self.assertEqual(result.stdout.count("File:"), 2)
        self.assertTrue(result.stdout.endswith(totals("2 files", 3, 4, 18, 2, 2)))

    def test_summary_reports_successes_and_failures(self):
        examples = (
            (("a.txt", "b.txt"), 2, 0),
            (("a.txt", "missing.txt", "b.txt"), 2, 1),
            (("missing1.txt", "missing2.txt"), 0, 2),
        )
        for paths, succeeded, failed in examples:
            with self.subTest(paths=paths):
                result = self.run_program(*paths)
                self.assertEqual(
                    summary_counts(result.stdout),
                    [f"Succeeded:  {succeeded}", f"Failed:     {failed}"],
                )

    def test_single_path_has_no_summary(self):
        for path in ("a.txt", "missing.txt"):
            with self.subTest(path=path):
                result = self.run_program(path)
                self.assertNotIn("Succeeded:", result.stdout)
                self.assertNotIn("Failed:", result.stdout)

    def test_permission_error_does_not_stop_processing(self):
        locked = str(self.directory / "locked.txt")
        real_open = open

        def fake_open(path, *args, **kwargs):
            if str(path) == locked:
                raise PermissionError(13, "Permission denied")
            return real_open(path, *args, **kwargs)

        good = str(self.directory / "a.txt")
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("builtins.open", fake_open):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = file_analyzer.main([locked, good])
        self.assertEqual(code, 1)
        self.assertIn(f"Permission denied when reading '{locked}'", stderr.getvalue())
        self.assertIn(block(good, 2, 3, 14, "three"), stdout.getvalue())
        self.assertIn(totals("1 file", 2, 3, 14, 1, 1), stdout.getvalue())

    def test_all_files_fail(self):
        result = self.run_program("missing1.txt", "missing2.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stderr.splitlines()), 2)
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0, 0, 2))

    def test_output_failure_stops_processing(self):
        read_end, write_end = os.pipe()
        os.close(read_end)  # With no reader, every write to the pipe fails.
        try:
            result = subprocess.run(
                [sys.executable, str(PROGRAM), "a.txt", "b.txt"],
                cwd=self.directory,
                stdout=write_end,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        finally:
            os.close(write_end)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "Error: Could not write the results.\n")


class TestR12CombinedTotals(MultiFileTestCase):
    def test_totals_add_up_every_file(self):
        self.write("café\r\n".encode(), "c.txt")  # 1 line, 1 word, 5 characters
        result = self.run_program("a.txt", "b.txt", "c.txt")
        self.assertTrue(result.stdout.endswith("\n\n" + totals("3 files", 4, 5, 23, 3, 0)))

    def test_totals_skip_failed_files(self):
        self.write(b"bad \xff", "bad.txt")
        result = self.run_program("a.txt", "bad.txt", "b.txt")
        self.assertTrue(result.stdout.endswith(totals("2 files", 3, 4, 18, 2, 1)))

    def test_one_successful_file_uses_singular(self):
        result = self.run_program("b.txt", "missing.txt")
        self.assertTrue(result.stdout.endswith(totals("1 file", 1, 1, 4, 1, 1)))

    def test_repeated_path_counts_twice(self):
        result = self.run_program("b.txt", "b.txt")
        self.assertTrue(result.stdout.endswith(totals("2 files", 2, 2, 8, 2, 0)))

    def test_empty_files_total_zero(self):
        self.write(b"", "empty1.txt")
        self.write(b"", "empty2.txt")
        result = self.run_program("empty1.txt", "empty2.txt")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.endswith(totals("2 files", 0, 0, 0, 2, 0)))

    def test_no_totals_for_a_single_path(self):
        for path in ("a.txt", "missing.txt"):
            with self.subTest(path=path):
                self.assertNotIn("Total", self.run_program(path).stdout)

    def test_large_totals(self):
        self.write(b"two words\n" * 100_000, "big1.txt")
        self.write(b"two words\n" * 50_000, "big2.txt")
        result = self.run_program("big1.txt", "big2.txt")
        self.assertTrue(
            result.stdout.endswith(totals("2 files", 150_000, 300_000, 1_500_000, 2, 0))
        )


class TestR13LongestWord(MultiFileTestCase):
    """R13: identify the longest word in each successfully analyzed file."""

    def assert_longest(self, content, expected):
        self.assertEqual(self.analyze(content).longest_word, expected)

    def test_finds_the_longest_word(self):
        self.assert_longest(b"cat elephant dog", "elephant")

    def test_searches_every_line(self):
        self.assert_longest(b"one\nthree\nseven\nfour", "three")

    def test_every_style_of_line_break_separates_words(self):
        self.assert_longest(b"ab\r\nabc\rabcd\nabcde", "abcde")

    def test_punctuation_is_part_of_the_word(self):
        self.assert_longest(b"see the end.", "end.")
        self.assert_longest(b"don't stop -- well-known", "well-known")

    def test_punctuation_only_piece_is_a_word(self):
        self.assert_longest(b"a -- b", "--")

    def test_unicode_whitespace_separates_words(self):
        self.assert_longest("ab abcd abc".encode(), "abcd")

    def test_keeps_original_letter_case(self):
        self.assert_longest(b"big HUGE Word", "HUGE")

    def test_leading_bom_is_not_part_of_the_word(self):
        self.assert_longest(b"\xef\xbb\xbfabc de", "abc")

    def test_longest_word_at_the_end_of_a_large_file(self):
        self.assert_longest(b"two words\n" * 100_000 + b"finally", "finally")

    def test_one_very_long_word(self):
        self.assert_longest(b"x" * 1_000_000, "x" * 1_000_000)

    def test_each_file_gets_its_own_longest_word(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertIn(longest_line("three"), result.stdout)
        self.assertIn(longest_line("four"), result.stdout)

    def test_failed_file_has_no_longest_word(self):
        result = self.run_program("a.txt", "missing.txt", "b.txt")
        self.assertEqual(result.stdout.count("Longest:"), 2)
        self.assertNotIn("Longest", result.stderr)


class TestR14LongestWordDisplay(MultiFileTestCase):
    """R14: show the longest word and its length with the other statistics."""

    def longest_output(self, content):
        self.write(content)
        result = self.run_program("notes.txt")
        self.assertEqual(result.returncode, 0)
        return result.stdout.splitlines()[-1]

    def test_exact_report_for_one_file(self):
        self.write(b"tiny elephant\n")
        result = self.run_program("notes.txt")
        self.assertEqual(
            result.stdout,
            "File:       notes.txt\n"
            "Lines:      1\n"
            "Words:      2\n"
            "Characters: 14\n"
            "Longest:    elephant (8 characters)\n",
        )
        self.assertEqual(result.returncode, 0)

    def test_length_of_one_is_singular(self):
        self.assertEqual(self.longest_output(b"a b c"), "Longest:    a (1 character)")

    def test_length_counts_code_points(self):
        examples = (
            ("café", "Longest:    café (4 characters)"),
            ("\U0001f600\U0001f600", "Longest:    \U0001f600\U0001f600 (2 characters)"),
            ("é", "Longest:    é (2 characters)"),
        )
        for content, expected in examples:
            with self.subTest(content=content):
                path = self.write(content.encode())
                # Run in-process so the terminal's encoding cannot affect the result.
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = file_analyzer.main([str(path)])
                self.assertEqual(code, 0)
                self.assertEqual(stdout.getvalue().splitlines()[-1], expected)

    def test_exact_output_for_several_files(self):
        result = self.run_program("a.txt", "missing.txt", "b.txt")
        self.assertEqual(
            result.stdout,
            "File:       a.txt\n"
            "Lines:      2\n"
            "Words:      3\n"
            "Characters: 14\n"
            "Longest:    three (5 characters)\n"
            "\n"
            "File:       b.txt\n"
            "Lines:      1\n"
            "Words:      1\n"
            "Characters: 4\n"
            "Longest:    four (4 characters)\n"
            "\n"
            "Total (2 files)\n"
            "Lines:      3\n"
            "Words:      4\n"
            "Characters: 18\n"
            "Succeeded:  2\n"
            "Failed:     1\n",
        )
        self.assertEqual(result.returncode, 1)

    def test_totals_block_has_no_longest_word(self):
        result = self.run_program("a.txt", "b.txt")
        totals_block = result.stdout.split("\n\n")[-1]
        self.assertEqual(totals_block, totals("2 files", 3, 4, 18, 2, 0))

    def test_unprintable_word_does_not_crash(self):
        self.write("日本".encode())
        env = {**os.environ, "PYTHONIOENCODING": "ascii", "PYTHONUTF8": "1"}
        result = self.run_program("notes.txt", env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Longest:    \\u65e5\\u672c (2 characters)\n", result.stdout)


class TestR15LongestWordTies(AnalyzerTestCase):
    """R15: when words share the maximum length, report the first one."""

    def assert_longest(self, content, expected):
        self.assertEqual(self.analyze(content).longest_word, expected)

    def test_first_word_on_a_line_wins(self):
        self.assert_longest(b"cat dog ant", "cat")

    def test_first_line_wins(self):
        self.assert_longest(b"abc\nxyz\r\nqrs", "abc")

    def test_tie_with_different_case(self):
        self.assert_longest(b"Word word WORD", "Word")

    def test_same_word_repeated(self):
        self.assert_longest(b"echo echo", "echo")

    def test_longer_word_after_a_tie_still_wins(self):
        self.assert_longest(b"ab cd abc abd", "abc")

    def test_first_is_shown_in_output(self):
        self.write(b"bird fish\nfrog")
        result = self.run_program("notes.txt")
        self.assertTrue(result.stdout.endswith("Longest:    bird (4 characters)\n"))


class TestR16NoWords(MultiFileTestCase):
    """R16: a file with no words shows N/A and a length of 0."""

    def assert_no_words(self, content):
        path = self.write(content)
        self.assertEqual(file_analyzer.analyze_file(path).longest_word, "")
        result = self.run_program("notes.txt")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.endswith("Longest:    N/A (0 characters)\n"))

    def test_empty_file(self):
        self.assert_no_words(b"")

    def test_only_whitespace(self):
        self.assert_no_words(" \t\n\r\n　".encode())

    def test_only_a_bom(self):
        self.assert_no_words(b"\xef\xbb\xbf")

    def test_word_spelled_n_a_is_a_real_word(self):
        self.write(b"N/A")
        result = self.run_program("notes.txt")
        self.assertTrue(result.stdout.endswith("Longest:    N/A (3 characters)\n"))

    def test_empty_file_among_others(self):
        self.write(b"", "empty.txt")
        result = self.run_program("a.txt", "empty.txt", "b.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn(block("empty.txt", 0, 0, 0, None), result.stdout)
        self.assertIn(block("a.txt", 2, 3, 14, "three"), result.stdout)
        self.assertTrue(result.stdout.endswith(totals("3 files", 3, 4, 18, 3, 0)))


class TestR17SucceededCount(MultiFileTestCase):
    """R17: the final summary shows the number of successfully analyzed files."""

    def test_line_follows_characters_in_the_summary(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertTrue(
            result.stdout.endswith(
                "Characters: 18\n" "Succeeded:  2\n" "Failed:     0\n"
            )
        )

    def test_counts_only_successful_files(self):
        self.write(b"bad \xff", "bad.txt")
        result = self.run_program("a.txt", "bad.txt", "missing.txt", "b.txt")
        self.assertIn("Succeeded:  2\n", result.stdout)

    def test_matches_the_totals_header(self):
        for paths, header in (
            (("a.txt", "b.txt", "a.txt"), "Total (3 files)"),
            (("b.txt", "missing.txt"), "Total (1 file)"),
            (("missing.txt", "missing.txt"), "Total (0 files)"),
        ):
            with self.subTest(paths=paths):
                stdout = self.run_program(*paths).stdout
                count = header.split("(")[1].split()[0]
                self.assertIn(header + "\n", stdout)
                self.assertIn(f"Succeeded:  {count}\n", stdout)

    def test_zero_when_every_file_fails(self):
        result = self.run_program("missing1.txt", "missing2.txt")
        self.assertEqual(summary_counts(result.stdout)[0], "Succeeded:  0")

    def test_empty_file_counts_as_a_success(self):
        self.write(b"", "empty.txt")
        result = self.run_program("empty.txt", "a.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(summary_counts(result.stdout)[0], "Succeeded:  2")

    def test_repeated_path_counts_each_time(self):
        result = self.run_program("b.txt", "b.txt", "b.txt")
        self.assertEqual(summary_counts(result.stdout)[0], "Succeeded:  3")

    def test_file_blocks_do_not_show_the_count(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertEqual(result.stdout.count("Succeeded:"), 1)
        for file_block in result.stdout.split("\n\n")[:-1]:
            self.assertNotIn("Succeeded:", file_block)

    def test_no_count_for_a_single_path(self):
        self.assertNotIn("Succeeded:", self.run_program("a.txt").stdout)


class TestR18FailedCount(MultiFileTestCase):
    """R18: the final summary shows the number of files that failed analysis."""

    def test_line_is_last_and_follows_succeeded(self):
        result = self.run_program("a.txt", "missing.txt", "b.txt")
        self.assertEqual(
            summary_counts(result.stdout), ["Succeeded:  2", "Failed:     1"]
        )
        self.assertTrue(result.stdout.endswith("Failed:     1\n"))

    def test_zero_is_shown_when_nothing_fails(self):
        result = self.run_program("a.txt", "b.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(summary_counts(result.stdout)[1], "Failed:     0")

    def test_every_kind_of_failure_is_counted(self):
        self.write(b"caf\xe9", "latin1.txt")
        self.write(b"ab\x00cd", "binary.txt")
        # Changed in Round 5: a directory is no longer an error (R19), so none is used here.
        result = self.run_program("latin1.txt", "binary.txt", "missing.txt", "a.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(summary_counts(result.stdout)[1], "Failed:     3")

    def test_permission_denied_is_counted(self):
        locked = str(self.directory / "locked.txt")
        real_open = open

        def fake_open(path, *args, **kwargs):
            if str(path) == locked:
                raise PermissionError(13, "Permission denied")
            return real_open(path, *args, **kwargs)

        stdout = io.StringIO()
        with mock.patch("builtins.open", fake_open):
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                code = file_analyzer.main([locked, str(self.directory / "a.txt")])
        self.assertEqual(code, 1)
        self.assertEqual(
            summary_counts(stdout.getvalue()), ["Succeeded:  1", "Failed:     1"]
        )

    def test_every_file_fails(self):
        result = self.run_program("missing1.txt", "missing2.txt", "missing3.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0, 0, 3))

    def test_repeated_failing_path_counts_each_time(self):
        result = self.run_program("missing.txt", "a.txt", "missing.txt")
        self.assertEqual(len(result.stderr.splitlines()), 2)
        self.assertEqual(summary_counts(result.stdout)[1], "Failed:     2")

    def test_counts_add_up_to_the_number_of_paths(self):
        paths = ("a.txt", "missing.txt", "b.txt", "a.txt", "gone.txt")
        result = self.run_program(*paths)
        succeeded, failed = (
            int(line.split()[-1]) for line in summary_counts(result.stdout)
        )
        self.assertEqual((succeeded, failed), (3, 2))
        self.assertEqual(succeeded + failed, len(paths))

    def test_failed_count_matches_error_messages(self):
        result = self.run_program("missing1.txt", "a.txt", "missing2.txt")
        self.assertEqual(
            summary_counts(result.stdout)[1],
            f"Failed:     {len(result.stderr.splitlines())}",
        )

    def test_no_count_for_a_single_failing_path(self):
        result = self.run_program("missing.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")


def inside(directory, name):
    """Return the path the program shows for a file found in a directory (R21)."""
    return os.path.join(str(directory), name)


class FakeEntry:
    """A stand-in for os.DirEntry, for listings that cannot be made on every system."""

    def __init__(self, name, is_file=True):
        self.name = name
        self._is_file = is_file

    def is_file(self):
        return self._is_file


class FakeListing:
    """A stand-in for the context manager that os.scandir returns."""

    def __init__(self, entries):
        self.entries = entries

    def __enter__(self):
        return iter(self.entries)

    def __exit__(self, *exc_info):
        return False


class DirectoryTestCase(AnalyzerTestCase):
    """Create a directory "notes" holding two .txt files whose statistics are easy to check."""

    def setUp(self):
        super().setUp()
        self.notes = self.directory / "notes"
        self.write(b"four", "notes/b.txt")  # 1 line, 1 word, 4 characters
        self.write(b"one two\nthree\n", "notes/A.txt")  # 2 lines, 3 words, 14 characters

    def run_in_process(self, *paths):
        """Run main() directly, so that os.scandir and open can be patched."""
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = file_analyzer.main([str(path) for path in paths])
        return code, stdout.getvalue(), stderr.getvalue()


class TestR19DirectoryInput(DirectoryTestCase):
    """R19: accept a directory path and analyze the regular .txt files directly inside it."""

    def test_analyzes_txt_files_in_a_directory(self):
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn(block(inside("notes", "A.txt"), 2, 3, 14, "three"), result.stdout)
        self.assertIn(block(inside("notes", "b.txt"), 1, 1, 4, "four"), result.stdout)

    def test_txt_match_ignores_case(self):
        self.write(b"x", "notes/c.TXT")
        self.write(b"y", "notes/d.Txt")
        result = self.run_program("notes")
        self.assertEqual(result.stdout.count("File:"), 4)
        self.assertIn(block(inside("notes", "c.TXT"), 1, 1, 1, "x"), result.stdout)
        self.assertIn(block(inside("notes", "d.Txt"), 1, 1, 1, "y"), result.stdout)

    def test_other_files_are_ignored_and_not_counted(self):
        for name in ("readme.md", "notes.txt.bak", "README", "datatxt", "c.text"):
            self.write(b"ignored words", "notes/" + name)
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.count("File:"), 2)
        self.assertNotIn("ignored", result.stdout)
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  2", "Failed:     0"])

    def test_directory_named_like_a_txt_file_is_not_a_regular_file(self):
        self.write(b"hidden words", "notes/old.txt/c.txt")
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertNotIn("old.txt", result.stdout)
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  2", "Failed:     0"])

    def test_hidden_and_bare_txt_names_are_included(self):
        self.write(b"h", "notes/.hidden.txt")
        self.write(b"t", "notes/.txt")
        result = self.run_program("notes")
        self.assertIn(block(inside("notes", ".hidden.txt"), 1, 1, 1, "h"), result.stdout)
        self.assertIn(block(inside("notes", ".txt"), 1, 1, 1, "t"), result.stdout)

    def test_directory_can_be_mixed_with_files(self):
        self.write(b"x", "x.txt")
        self.write(b"y", "y.txt")
        result = self.run_program("x.txt", "notes", "y.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout,
            block("x.txt", 1, 1, 1, "x")
            + "\n"
            + block(inside("notes", "A.txt"), 2, 3, 14, "three")
            + "\n"
            + block(inside("notes", "b.txt"), 1, 1, 4, "four")
            + "\n"
            + block("y.txt", 1, 1, 1, "y")
            + "\n"
            + totals("4 files", 5, 6, 20, 4, 0),
        )

    def test_several_directories(self):
        self.write(b"z", "more/z.txt")
        result = self.run_program("more", "notes")
        self.assertEqual(result.returncode, 0)
        self.assertLess(
            result.stdout.index(inside("more", "z.txt")),
            result.stdout.index(inside("notes", "A.txt")),
        )
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  3", "Failed:     0"])

    def test_directory_given_twice_is_analyzed_twice(self):
        result = self.run_program("notes", "notes")
        self.assertEqual(result.stdout.count("File:"), 4)
        self.assertTrue(result.stdout.endswith(totals("4 files", 6, 8, 36, 4, 0)))

    def test_file_in_directory_and_given_directly_counts_twice(self):
        result = self.run_program("notes", "notes/b.txt")
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  3", "Failed:     0"])

    def test_absolute_directory_path(self):
        absolute = self.notes.resolve()
        result = self.run_program(absolute)
        self.assertEqual(result.returncode, 0)
        self.assertIn(block(inside(absolute, "A.txt"), 2, 3, 14, "three"), result.stdout)

    def test_directory_with_spaces_in_its_name(self):
        self.write(b"x", "my notes/c d.txt")
        result = self.run_program("my notes")
        self.assertEqual(result.returncode, 0)
        self.assertIn(block(inside("my notes", "c d.txt"), 1, 1, 1, "x"), result.stdout)

    def test_current_directory(self):
        self.write(b"x", "c.txt")
        result = self.run_program(".")
        self.assertEqual(result.returncode, 0)
        self.assertIn(block(inside(".", "c.txt"), 1, 1, 1, "x"), result.stdout)

    def test_missing_directory_is_not_found(self):
        result = self.run_program("missing")
        self.assertEqual(result.returncode, 1)
        self.assertIn("'missing' was not found", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_symbolic_link_to_a_file_is_included_and_broken_link_skipped(self):
        try:
            os.symlink(self.notes / "b.txt", self.notes / "link.txt")
            os.symlink(self.notes / "gone", self.notes / "broken.txt")
        except (OSError, NotImplementedError):
            self.skipTest("this system does not allow creating symbolic links")
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn(block(inside("notes", "link.txt"), 1, 1, 4, "four"), result.stdout)
        self.assertNotIn("broken.txt", result.stdout)

    def test_help_mentions_directories(self):
        result = self.run_program("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("directory", result.stdout)


class TestR20DirectoryOrder(DirectoryTestCase):
    """R20: do not search subdirectories, and process files in alphabetical order."""

    def file_lines(self, stdout):
        return [line for line in stdout.splitlines() if line.startswith("File:")]

    def test_subdirectories_are_not_searched(self):
        self.write(b"deep", "notes/old/c.txt")
        self.write(b"deeper", "notes/old/older/d.txt")
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("File:"), 2)
        self.assertNotIn("deep", result.stdout)
        self.assertNotIn("old", result.stdout)

    def test_alphabetical_order_ignores_case(self):
        for name in ("Zed.txt", "Cat.TXT", "apple.txt"):
            self.write(b"w", "notes/" + name)
        result = self.run_program("notes")
        # A plain code-point sort would put every capital letter first.
        expected = ["A.txt", "apple.txt", "b.txt", "Cat.TXT", "Zed.txt"]
        self.assertEqual(
            self.file_lines(result.stdout),
            [f"File:       {inside('notes', name)}" for name in expected],
        )

    def test_order_is_alphabetical_not_creation_order(self):
        self.write(b"w", "notes/0.txt")  # created last, but sorts first
        result = self.run_program("notes")
        self.assertEqual(
            self.file_lines(result.stdout),
            [f"File:       {inside('notes', name)}" for name in ("0.txt", "A.txt", "b.txt")],
        )

    def test_sorting_compares_characters_not_numbers(self):
        for name in ("2.txt", "10.txt", "1.txt"):
            self.write(b"n", "more/" + name)
        result = self.run_program("more")
        self.assertEqual(
            self.file_lines(result.stdout),
            [f"File:       {inside('more', name)}" for name in ("1.txt", "10.txt", "2.txt")],
        )

    def test_names_that_differ_only_in_case_are_ordered_by_exact_name(self):
        # Two such names cannot exist together on Windows, so the listing is simulated.
        entries = [FakeEntry(name) for name in ("b.txt", "a.txt", "B.txt", "A.txt")]
        with mock.patch("os.scandir", return_value=FakeListing(entries)):
            paths = file_analyzer.list_text_files("notes")
        self.assertEqual(
            paths, [inside("notes", name) for name in ("A.txt", "a.txt", "B.txt", "b.txt")]
        )

    def test_listing_keeps_only_regular_txt_files(self):
        entries = [
            FakeEntry("c.txt"),
            FakeEntry("sub.txt", is_file=False),
            FakeEntry("readme.md"),
            FakeEntry("A.TXT"),
        ]
        with mock.patch("os.scandir", return_value=FakeListing(entries)):
            paths = file_analyzer.list_text_files("notes")
        self.assertEqual(paths, [inside("notes", "A.TXT"), inside("notes", "c.txt")])


class TestR21DirectoryFileStatistics(DirectoryTestCase):
    """R21: show each analyzed .txt file in a directory in the existing block format."""

    def test_exact_output_for_a_directory(self):
        result = self.run_program("notes")
        self.assertEqual(
            result.stdout,
            block(inside("notes", "A.txt"), 2, 3, 14, "three")
            + "\n"
            + block(inside("notes", "b.txt"), 1, 1, 4, "four")
            + "\n"
            + totals("2 files", 3, 4, 18, 2, 0),
        )

    def test_file_line_joins_the_directory_as_typed(self):
        result = self.run_program("notes/")
        self.assertIn(f"File:       {inside('notes/', 'A.txt')}\n", result.stdout)

    def test_every_statistic_is_shown_for_each_file(self):
        self.write(b"", "notes/empty.txt")
        self.write("café\r\n".encode(), "notes/cafe.txt")
        result = self.run_program("notes")
        self.assertIn(block(inside("notes", "empty.txt"), 0, 0, 0, None), result.stdout)
        self.assertIn(block(inside("notes", "cafe.txt"), 1, 1, 5, "café"), result.stdout)

    def test_longest_word_tie_keeps_the_first_word_in_each_file(self):
        self.write(b"cat dog ant", "notes/c.txt")
        result = self.run_program("notes")
        self.assertIn(block(inside("notes", "c.txt"), 1, 3, 11, "cat"), result.stdout)


class TestR22DirectoryTotals(DirectoryTestCase):
    """R22: show combined totals with the success and failure counts for directory analysis."""

    def test_summary_for_a_directory(self):
        result = self.run_program("notes")
        self.assertTrue(result.stdout.endswith("\n\n" + totals("2 files", 3, 4, 18, 2, 0)))

    def test_summary_for_a_directory_with_one_file(self):
        self.write(b"x", "single/only.txt")
        result = self.run_program("single")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout,
            block(inside("single", "only.txt"), 1, 1, 1, "x")
            + "\n"
            + totals("1 file", 1, 1, 1, 1, 0),
        )

    def test_empty_directory_shows_a_zero_summary(self):
        (self.directory / "empty").mkdir()
        result = self.run_program("empty")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0, 0, 0))

    def test_directory_without_txt_files_shows_a_zero_summary(self):
        self.write(b"words here", "docs/readme.md")
        result = self.run_program("docs")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0, 0, 0))

    def test_totals_include_directory_files_and_direct_files(self):
        self.write(b"x y", "x.txt")  # 1 line, 2 words, 3 characters
        result = self.run_program("notes", "x.txt")
        self.assertTrue(result.stdout.endswith(totals("3 files", 4, 6, 21, 3, 0)))

    def test_totals_skip_failed_files_and_count_them(self):
        self.write(b"bad \xff", "notes/bad.txt")
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.endswith(totals("2 files", 3, 4, 18, 2, 1)))

    def test_single_file_path_still_has_no_summary(self):
        result = self.run_program("notes/b.txt")
        self.assertEqual(result.stdout, block("notes/b.txt", 1, 1, 4, "four"))


class TestR23DirectoryErrors(DirectoryTestCase):
    """R23: report a .txt file that cannot be read and continue with the rest."""

    def test_unreadable_file_is_reported_and_the_rest_continue(self):
        self.write(b"caf\xe9", "notes/Apple.txt")  # sorts between A.txt and b.txt
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            f"Error: '{inside('notes', 'Apple.txt')}' is not valid UTF-8. "
            "Only UTF-8 text is supported.\n",
        )
        self.assertEqual(
            result.stdout,
            block(inside("notes", "A.txt"), 2, 3, 14, "three")
            + "\n"
            + block(inside("notes", "b.txt"), 1, 1, 4, "four")
            + "\n"
            + totals("2 files", 3, 4, 18, 2, 1),
        )

    def test_every_kind_of_file_error_is_reported_and_counted(self):
        self.write(b"caf\xe9", "notes/latin1.txt")
        self.write(b"ab\x00cd", "notes/binary.txt")
        self.write("hello".encode("utf-16"), "notes/utf16.txt")
        result = self.run_program("notes")
        self.assertEqual(result.returncode, 1)
        errors = result.stderr.splitlines()
        self.assertEqual(len(errors), 3)
        self.assertIn(f"'{inside('notes', 'binary.txt')}' appears to be binary", errors[0])
        self.assertIn(f"'{inside('notes', 'latin1.txt')}' is not valid UTF-8", errors[1])
        self.assertIn(f"'{inside('notes', 'utf16.txt')}' is not valid UTF-8", errors[2])
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  2", "Failed:     3"])

    def test_permission_denied_file_is_reported_and_the_rest_continue(self):
        locked = inside(self.notes, "A.txt")
        real_open = open

        def fake_open(path, *args, **kwargs):
            if str(path) == locked:
                raise PermissionError(13, "Permission denied")
            return real_open(path, *args, **kwargs)

        with mock.patch("builtins.open", fake_open):
            code, stdout, stderr = self.run_in_process(self.notes)
        self.assertEqual(code, 1)
        self.assertIn(f"Permission denied when reading '{locked}'", stderr)
        self.assertEqual(
            stdout,
            block(inside(self.notes, "b.txt"), 1, 1, 4, "four")
            + "\n"
            + totals("1 file", 1, 1, 4, 1, 1),
        )

    def test_file_removed_after_listing_is_reported(self):
        gone = FakeEntry("0gone.txt")
        entries = [gone, FakeEntry("A.txt"), FakeEntry("b.txt")]
        with mock.patch("os.scandir", return_value=FakeListing(entries)):
            code, stdout, stderr = self.run_in_process(self.notes)
        self.assertEqual(code, 1)
        self.assertIn(f"'{inside(self.notes, '0gone.txt')}' was not found", stderr)
        self.assertTrue(stdout.endswith(totals("2 files", 3, 4, 18, 2, 1)))

    def test_every_file_in_the_directory_fails(self):
        self.write(b"\xff", "bad/one.txt")
        self.write(b"\xff", "bad/two.txt")
        result = self.run_program("bad")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stderr.splitlines()), 2)
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0, 0, 2))

    def test_directory_that_cannot_be_listed_is_one_failure(self):
        self.write(b"x y", "x.txt")
        error = PermissionError(13, "Permission denied")
        with mock.patch("os.scandir", side_effect=error):
            code, stdout, stderr = self.run_in_process(self.notes, self.directory / "x.txt")
        self.assertEqual(code, 1)
        self.assertEqual(
            stderr, f"Error: Permission denied when reading directory '{self.notes}'.\n"
        )
        self.assertEqual(
            stdout,
            block(self.directory / "x.txt", 1, 2, 3, "x")
            + "\n"
            + totals("1 file", 1, 2, 3, 1, 1),
        )

    def test_other_listing_failure_explains_why(self):
        error = OSError(5, "Input/output error")
        with mock.patch("os.scandir", side_effect=error):
            code, stdout, stderr = self.run_in_process(self.notes)
        self.assertEqual(code, 1)
        self.assertEqual(
            stderr, f"Error: Could not read directory '{self.notes}': Input/output error.\n"
        )
        self.assertEqual(stdout, totals("0 files", 0, 0, 0, 0, 1))

    def test_errors_in_one_directory_do_not_stop_the_next_path(self):
        self.write(b"\xff", "notes/bad.txt")
        self.write(b"x", "x.txt")
        result = self.run_program("notes", "x.txt")
        self.assertEqual(result.returncode, 1)
        self.assertIn(block("x.txt", 1, 1, 1, "x"), result.stdout)
        self.assertEqual(summary_counts(result.stdout), ["Succeeded:  3", "Failed:     1"])


if __name__ == "__main__":
    unittest.main()

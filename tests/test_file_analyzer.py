"""Automated tests, with one test class for each requirement (R1-R6, R9-R16)."""

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

    def test_directory(self):
        self.assert_error(self.run_program("."), "is a directory")

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


def totals(header, lines, words, characters):
    return (
        f"Total ({header})\n"
        f"Lines:      {lines}\n"
        f"Words:      {words}\n"
        f"Characters: {characters}\n"
    )


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
            + totals("2 files", 3, 4, 18),
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
            + totals("2 files", 3, 4, 18),
        )

    def test_failure_first_or_last(self):
        for paths in (("missing.txt", "a.txt"), ("a.txt", "missing.txt")):
            with self.subTest(paths=paths):
                result = self.run_program(*paths)
                self.assertEqual(result.returncode, 1)
                self.assertIn("'missing.txt' was not found", result.stderr)
                self.assertEqual(
                    result.stdout,
                    block("a.txt", 2, 3, 14, "three") + "\n" + totals("1 file", 2, 3, 14),
                )

    def test_every_kind_of_error_is_reported_and_skipped(self):
        self.write(b"caf\xe9", "latin1.txt")
        self.write(b"ab\x00cd", "binary.txt")
        (self.directory / "folder").mkdir()
        result = self.run_program(
            "latin1.txt", "a.txt", "folder", "binary.txt", "missing.txt", "b.txt"
        )
        self.assertEqual(result.returncode, 1)
        errors = result.stderr.splitlines()
        self.assertEqual(len(errors), 4)
        self.assertIn("'latin1.txt' is not valid UTF-8", errors[0])
        self.assertIn("'folder' is a directory", errors[1])
        self.assertIn("'binary.txt' appears to be binary", errors[2])
        self.assertIn("'missing.txt' was not found", errors[3])
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout.count("File:"), 2)
        self.assertNotIn("latin1.txt", result.stdout)

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
        self.assertIn(totals("1 file", 2, 3, 14), stdout.getvalue())

    def test_all_files_fail(self):
        result = self.run_program("missing1.txt", "missing2.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stderr.splitlines()), 2)
        self.assertEqual(result.stdout, totals("0 files", 0, 0, 0))

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
        self.assertTrue(result.stdout.endswith("\n\n" + totals("3 files", 4, 5, 23)))

    def test_totals_skip_failed_files(self):
        self.write(b"bad \xff", "bad.txt")
        result = self.run_program("a.txt", "bad.txt", "b.txt")
        self.assertTrue(result.stdout.endswith(totals("2 files", 3, 4, 18)))

    def test_one_successful_file_uses_singular(self):
        result = self.run_program("b.txt", "missing.txt")
        self.assertTrue(result.stdout.endswith(totals("1 file", 1, 1, 4)))

    def test_repeated_path_counts_twice(self):
        result = self.run_program("b.txt", "b.txt")
        self.assertTrue(result.stdout.endswith(totals("2 files", 2, 2, 8)))

    def test_empty_files_total_zero(self):
        self.write(b"", "empty1.txt")
        self.write(b"", "empty2.txt")
        result = self.run_program("empty1.txt", "empty2.txt")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.endswith(totals("2 files", 0, 0, 0)))

    def test_no_totals_for_a_single_path(self):
        for path in ("a.txt", "missing.txt"):
            with self.subTest(path=path):
                self.assertNotIn("Total", self.run_program(path).stdout)

    def test_large_totals(self):
        self.write(b"two words\n" * 100_000, "big1.txt")
        self.write(b"two words\n" * 50_000, "big2.txt")
        result = self.run_program("big1.txt", "big2.txt")
        self.assertTrue(
            result.stdout.endswith(totals("2 files", 150_000, 300_000, 1_500_000))
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
            "Characters: 18\n",
        )
        self.assertEqual(result.returncode, 1)

    def test_totals_block_has_no_longest_word(self):
        result = self.run_program("a.txt", "b.txt")
        totals_block = result.stdout.split("\n\n")[-1]
        self.assertEqual(totals_block, totals("2 files", 3, 4, 18))

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
        self.assertTrue(result.stdout.endswith(totals("3 files", 3, 4, 18)))


if __name__ == "__main__":
    unittest.main()

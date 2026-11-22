"""Automated tests, with one test class for each requirement (R1-R6)."""

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
            "Characters: 14\n",
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
            "Characters: 0\n",
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

    def test_extra_argument(self):
        result = self.run_program("one.txt", "two.txt")
        self.assert_error(result, "usage: file_analyzer.py", code=2)
        self.assertIn("unrecognized arguments: two.txt", result.stderr)

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


if __name__ == "__main__":
    unittest.main()

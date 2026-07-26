"""Tests for the Typer command-line interface."""

import pytest

typer = pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from bambara_normalizer import __version__  # noqa: E402
from bambara_normalizer.cli import app, main  # noqa: E402

runner = CliRunner()


def invoke(*args, **kwargs):
    return runner.invoke(app, list(args), **kwargs)


class TestNormalizeCommand:
    def test_expands_contractions_by_default(self):
        result = invoke("B'a fɔ́")
        assert result.exit_code == 0
        assert result.stdout.strip() == "bɛ a fɔ́"

    def test_contract_mode(self):
        result = invoke("--mode", "contract", "bɛ a fɔ")
        assert result.exit_code == 0
        assert result.stdout.strip() == "b'a fɔ"

    def test_wer_preset(self):
        result = invoke("--preset", "wer", "K'a fɔ́!")
        assert result.exit_code == 0
        assert result.stdout.strip() == "ka a fɔ"

    def test_reads_stdin(self):
        result = invoke(input="B'a fɔ́\n")
        assert result.exit_code == 0
        assert result.stdout.strip() == "bɛ a fɔ́"

    def test_joins_unquoted_words(self):
        result = invoke("B'a", "fɔ́")
        assert result.exit_code == 0
        assert result.stdout.strip() == "bɛ a fɔ́"

    def test_expand_numbers_flag(self):
        result = invoke("--expand-numbers", "A ye 42 di")
        assert result.exit_code == 0
        assert "bi naani ni fila" in result.stdout

    def test_version(self):
        result = invoke("--version")
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_help_lists_the_options(self):
        result = invoke("--help")
        assert result.exit_code == 0
        assert "--preset" in result.stdout
        assert "--evaluate" in result.stdout


class TestFileProcessing:
    def test_normalizes_a_file_to_stdout(self, tmp_path):
        source = tmp_path / "corpus.txt"
        source.write_text("B'a fɔ́\nk'a ta\n", encoding="utf-8")

        result = invoke("--input", str(source))

        assert result.exit_code == 0
        assert result.stdout.splitlines() == ["bɛ a fɔ́", "ka a ta"]

    def test_writes_to_output_file(self, tmp_path):
        source = tmp_path / "corpus.txt"
        source.write_text("B'a fɔ́\nk'a ta\n", encoding="utf-8")
        destination = tmp_path / "normalized.txt"

        result = invoke("--input", str(source), "--output", str(destination))

        assert result.exit_code == 0
        assert destination.read_text(encoding="utf-8") == "bɛ a fɔ́\nka a ta\n"

    def test_rejects_file_and_text_together(self, tmp_path):
        source = tmp_path / "corpus.txt"
        source.write_text("B'a fɔ́\n", encoding="utf-8")

        result = invoke("--input", str(source), "hello")

        assert result.exit_code == 1


class TestEvaluate:
    def _pair(self, tmp_path):
        reference = tmp_path / "ref.txt"
        hypothesis = tmp_path / "hyp.txt"
        reference.write_text("B'a fɔ́\nk'a ta\n", encoding="utf-8")
        hypothesis.write_text("bɛ a fɔ\nka a ta\n", encoding="utf-8")
        return reference, hypothesis

    def test_reports_wer_and_cer(self, tmp_path):
        reference, hypothesis = self._pair(tmp_path)

        result = invoke("--evaluate", str(reference), str(hypothesis))

        assert result.exit_code == 0
        assert "WER" in result.stdout
        assert "CER" in result.stdout

    def test_detailed_adds_per_utterance_rows(self, tmp_path):
        reference, hypothesis = self._pair(tmp_path)

        result = invoke("--evaluate", "--detailed", str(reference), str(hypothesis))

        assert result.exit_code == 0
        assert "Per-utterance" in result.stdout

    def test_requires_two_files(self, tmp_path):
        reference, _ = self._pair(tmp_path)

        result = invoke("--evaluate", str(reference))

        assert result.exit_code == 1

    def test_rejects_mismatched_line_counts(self, tmp_path):
        reference, hypothesis = self._pair(tmp_path)
        hypothesis.write_text("bɛ a fɔ\n", encoding="utf-8")

        result = invoke("--evaluate", str(reference), str(hypothesis))

        assert result.exit_code == 1


class TestMainEntryPoint:
    def test_returns_zero_on_success(self, capsys):
        assert main(["--preset", "wer", "K'a fɔ́!"]) == 0
        assert capsys.readouterr().out.strip() == "ka a fɔ"

    def test_returns_usage_error_code(self):
        assert main(["--preset", "bogus", "x"]) == 2

    def test_returns_one_on_missing_file(self, tmp_path):
        assert main(["--input", str(tmp_path / "absent.txt")]) == 1

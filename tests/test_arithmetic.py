"""Arithmetic normalization tests."""

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    arithmetic_to_bambara,
    find_arithmetic_spans,
    format_arithmetic_bambara,
    is_arithmetic_operator,
    normalize,
    normalize_arithmetic_in_text,
)


class TestArithmeticToBambara:
    def test_addition(self):
        assert arithmetic_to_bambara(2, "+", 2) == "fila fara fila kan"

    def test_subtraction_reverses_the_operands(self):
        assert arithmetic_to_bambara(8, "-", 5) == "duuru bɔ seegin na"

    def test_multiplication(self):
        assert arithmetic_to_bambara(5, "×", 3) == "duuru siɲɛ saba"

    def test_division(self):
        assert arithmetic_to_bambara(10, "÷", 2) == "tan tila fila la"

    def test_result(self):
        assert arithmetic_to_bambara(2, "+", 2, result=4) == "fila fara fila kan, o ye naani ye"

    def test_postposition_follows_the_preceding_word(self):
        # `la` after a vowel, `na` after a nasal.
        assert arithmetic_to_bambara(9, "-", 4).endswith("kɔnɔntɔn na")
        assert arithmetic_to_bambara(100, "-", 4).endswith("kɛmɛ la")
        assert arithmetic_to_bambara(9, "÷", 3).endswith("saba la")
        assert arithmetic_to_bambara(9, "÷", 1).endswith("kelen na")

    def test_decimals(self):
        assert arithmetic_to_bambara(1.5, "+", 2) == "kelen tomi duuru fara fila kan"

    @pytest.mark.parametrize("alias,expected", [("*", "×"), ("x", "×"), ("/", "÷")])
    def test_ascii_aliases(self, alias, expected):
        assert arithmetic_to_bambara(6, alias, 2) == arithmetic_to_bambara(6, expected, 2)

    def test_rejects_a_non_operator(self):
        with pytest.raises(ValueError):
            arithmetic_to_bambara(2, ":", 2)

    def test_rejects_equals_as_the_operator(self):
        with pytest.raises(ValueError):
            arithmetic_to_bambara(2, "=", 2)


class TestFormatArithmeticBambara:
    @pytest.mark.parametrize(
        "expression,expected",
        [
            ("2 + 2", "fila fara fila kan"),
            ("2+2", "fila fara fila kan"),
            ("8 - 5", "duuru bɔ seegin na"),
            ("8−5", "duuru bɔ seegin na"),
            ("5 × 3", "duuru siɲɛ saba"),
            ("5*3", "duuru siɲɛ saba"),
            ("5 x 3", "duuru siɲɛ saba"),
            ("10 / 2", "tan tila fila la"),
            ("2+2=4", "fila fara fila kan, o ye naani ye"),
        ],
    )
    def test_written_forms(self, expression, expected):
        assert format_arithmetic_bambara(expression) == expected

    @pytest.mark.parametrize("expression", ["1 + 2 + 3", "20-22-33-44", "2024-01-05", "42"])
    def test_rejects_what_is_not_a_two_operand_operation(self, expression):
        with pytest.raises(ValueError):
            format_arithmetic_bambara(expression)


class TestArithmeticTextNormalization:
    def test_normalizes_an_expression_in_a_sentence(self):
        assert normalize_arithmetic_in_text("A ko 2 + 2 = 4") == (
            "A ko fila fara fila kan, o ye naani ye"
        )

    def test_preserves_surrounding_text_and_punctuation(self):
        assert normalize_arithmetic_in_text("Kalanden ye 3 × 4 sɛbɛn, o ka nɔgɔn.") == (
            "Kalanden ye saba siɲɛ naani sɛbɛn, o ka nɔgɔn."
        )

    def test_normalizes_several_expressions(self):
        assert normalize_arithmetic_in_text("2+2 ani 10/2") == (
            "fila fara fila kan ani tan tila fila la"
        )

    def test_trailing_punctuation_is_not_part_of_the_expression(self):
        assert normalize_arithmetic_in_text("A ko 2 + 2 = 4.") == (
            "A ko fila fara fila kan, o ye naani ye."
        )

    def test_leaves_a_year_range_alone(self):
        assert normalize_arithmetic_in_text("A wolola 2020-2021 la") == "A wolola 2020-2021 la"

    def test_leaves_a_month_and_year_alone(self):
        assert normalize_arithmetic_in_text("sugu la 10/2025") == "sugu la 10/2025"

    def test_leaves_a_phone_number_alone(self):
        assert normalize_arithmetic_in_text("Telefɔni 20-22-33-44") == "Telefɔni 20-22-33-44"

    def test_leaves_a_bare_number_alone(self):
        assert normalize_arithmetic_in_text("A ye 42 di") == "A ye 42 di"

    def test_spaced_operator_still_reads_a_year_range_as_arithmetic(self):
        # The guard only covers the tight form: with spaces it is an operation.
        assert normalize_arithmetic_in_text("2021 - 2020") == (
            "waa fila ni mugan bɔ waa fila ni mugan ni kelen na"
        )

    def test_a_lone_x_is_not_multiplication(self):
        assert normalize_arithmetic_in_text("5x3") == "5x3"


class TestArithmeticSpans:
    def test_the_whole_expression_is_one_span(self):
        spans = find_arithmetic_spans("A ko 2 + 2 = 4 bi")
        assert [(s.source, s.kind) for s in spans] == [("2 + 2 = 4", "arithmetic")]

    def test_unreadable_expression_reserves_nothing(self):
        assert find_arithmetic_spans("Telefɔni 20-22-33-44") == []


class TestArithmeticNormalizerIntegration:
    def test_with_expand_arithmetic(self):
        result = normalize("A ko 2 + 2", expand_arithmetic=True)
        assert result == "a ko fila fara fila kan"

    def test_without_expand_arithmetic(self):
        result = normalize("A ko 2 + 2", expand_arithmetic=False, remove_punctuation=False)
        assert "2 + 2" in result

    def test_wer_preset_expands_arithmetic(self, wer_normalizer):
        assert wer_normalizer("A ko 12 + 8 = 20") == (
            "a ko tan ni fila fara seegin kan o ye mugan ye"
        )

    def test_numbers_alone_do_not_break_up_an_expression(self):
        config = BambaraNormalizerConfig(
            expand_numbers=True,
            expand_arithmetic=False,
            remove_punctuation=False,
        )
        assert "2 + 2" in BambaraNormalizer(config)("A ko 2 + 2")

    def test_dates_win_over_arithmetic(self):
        config = BambaraNormalizerConfig(
            expand_arithmetic=True,
            expand_dates=True,
            remove_punctuation=False,
        )
        assert "desanburu" in BambaraNormalizer(config)("A bɛ na 24-12-2025 la")


class TestArithmeticOperators:
    @pytest.mark.parametrize("symbol", ["+", "-", "−", "×", "*", "÷", "/", "=", "x"])
    def test_known_operators(self, symbol):
        assert is_arithmetic_operator(symbol)

    @pytest.mark.parametrize("symbol", [":", ".", "%", "ni"])
    def test_unknown_operators(self, symbol):
        assert not is_arithmetic_operator(symbol)

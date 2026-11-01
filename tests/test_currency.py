"""Currency normalization tests."""

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    currency_to_bambara,
    find_numeric_spans,
    normalize_currency_in_text,
    normalize_numeric_expressions,
)


class TestCurrencyToBambara:
    @pytest.mark.parametrize(
        "currency",
        ["FCFA", "F CFA", "F.CFA", "CFA", "XOF", "F", "franc", "francs", "francs CFA"],
    )
    def test_every_cfa_spelling_reads_as_sefa_wari(self, currency):
        assert currency_to_bambara(5000, currency) == "sefa wari waa kelen"

    @pytest.mark.parametrize(
        ("currency", "expected"),
        [
            ("€", "ero wari tan"),
            ("EUR", "ero wari tan"),
            ("euros", "ero wari tan"),
            ("$", "dolari wari tan"),
            ("USD", "dolari wari tan"),
            ("dollars", "dolari wari tan"),
            ("£", "livuru wari tan"),
            ("GBP", "livuru wari tan"),
        ],
    )
    def test_foreign_currencies_keep_their_face_value(self, currency, expected):
        assert currency_to_bambara(10, currency) == expected

    def test_currency_names_are_case_insensitive(self):
        assert currency_to_bambara(10, "fcfa") == "sefa wari dɔrɔmɛ fila"
        assert currency_to_bambara(10, "Euros") == "ero wari tan"

    def test_amount_given_as_written_text(self):
        """Written amounts follow the number rules: grouped thousands, decimal comma."""
        assert currency_to_bambara("1 000", "FCFA") == "sefa wari kɛmɛ fila"
        assert currency_to_bambara("1.000", "FCFA") == "sefa wari kɛmɛ fila"
        assert currency_to_bambara("15,50", "€") == "ero wari tan ni duuru tomi duuru"

    def test_unknown_currency_raises(self):
        with pytest.raises(ValueError):
            currency_to_bambara(10, "naira")


class TestCfaIsCountedInDorome:
    """
    Below a million, the amount said after "sefa wari" is the number of dɔrɔmɛ, the
    five-franc coin. Millions keep their face value.
    """

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            (1250, "sefa wari kɛmɛ fila ni bi duuru"),
            ("20 000", "sefa wari waa naani"),
            ("100 000", "sefa wari waa mugan"),
        ],
    )
    def test_amount_below_a_million_is_divided_by_five(self, amount, expected):
        assert currency_to_bambara(amount, "FCFA") == expected

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("600 000", "sefa wari waa kɛmɛ ni waa mugan"),
            ("625 000", "sefa wari waa kɛmɛ ni waa mugan ni duuru"),
        ],
    )
    def test_hundreds_of_thousands_and_thousands_each_take_waa(self, amount, expected):
        assert currency_to_bambara(amount, "FCFA") == expected

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("601 000", "sefa wari waa kɛmɛ ni waa mugan ani kɛmɛ fila"),
            ("602 500", "sefa wari waa kɛmɛ ni waa mugan ani kɛmɛ duuru"),
        ],
    )
    def test_part_below_a_thousand_dorome_is_joined_with_ani(self, amount, expected):
        assert currency_to_bambara(amount, "FCFA") == expected

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            ("1 000 000", "sefa wari miliyɔn kelen"),
            ("1 100 000", "sefa wari miliyɔn kelen ni waa mugan"),
            ("1 500 000", "sefa wari miliyɔn kelen ni waa kɛmɛ"),
            ("2 000 500", "sefa wari miliyɔn fila ani dɔrɔmɛ kɛmɛ"),
        ],
    )
    def test_millions_keep_their_face_value(self, amount, expected):
        assert currency_to_bambara(amount, "FCFA") == expected

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [(7, "sefa wari dɔrɔmɛ kelen tomi naani"), ("2,5", "sefa wari dɔrɔmɛ fu tomi duuru")],
    )
    def test_amount_not_a_multiple_of_five_is_never_rounded(self, amount, expected):
        """Rounding to the nearest coin would silently change the amount the listener hears."""
        assert currency_to_bambara(amount, "FCFA") == expected

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            (25, "sefa wari dɔrɔmɛ duuru"),
            (200, "sefa wari dɔrɔmɛ bi naani"),
            (500, "sefa wari dɔrɔmɛ kɛmɛ"),
            (995, "sefa wari dɔrɔmɛ kɛmɛ ni bi kɔnɔntɔn ni kɔnɔntɔn"),
            ("620 250", "sefa wari waa kɛmɛ ni waa mugan ni naani ani dɔrɔmɛ bi duuru"),
            ("1 000 005", "sefa wari miliyɔn kelen ani dɔrɔmɛ kelen"),
        ],
    )
    def test_part_under_a_thousand_francs_names_the_dorome(self, amount, expected):
        """
        Under 1 000 FCFA (fewer than two hundred dɔrɔmɛ) the coin is named; from
        "kɛmɛ fila" upwards it is not.
        """
        assert currency_to_bambara(amount, "FCFA") == expected

    def test_amount_written_in_dorome_is_not_divided_again(self):
        assert currency_to_bambara(500, "dɔrɔmɛ") == "dɔrɔmɛ kɛmɛ duuru"


class TestNormalizeCurrencyInText:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("A ye 5 000 FCFA sara.", "A ye sefa wari waa kelen sara."),
            ("1.000 FCFA", "sefa wari kɛmɛ fila"),
            ("2 500 francs CFA", "sefa wari kɛmɛ duuru"),
            ("5000F", "sefa wari waa kelen"),
            ("XOF 5 000", "sefa wari waa kelen"),
            ("20 $", "dolari wari mugan"),
            ("$20", "dolari wari mugan"),
            ("$ 20", "dolari wari mugan"),
            ("€15,50", "ero wari tan ni duuru tomi duuru"),
            ("£100", "livuru wari kɛmɛ"),
            ("A ye 500 dɔrɔmɛ di.", "A ye dɔrɔmɛ kɛmɛ duuru di."),
        ],
    )
    def test_amount_and_currency_become_one_phrase(self, text, expected):
        assert normalize_currency_in_text(text) == expected

    def test_letter_f_starting_a_word_is_not_a_currency(self):
        assert normalize_currency_in_text("5 Fanta") == "5 Fanta"

    def test_lowercase_f_is_not_a_currency(self):
        """Only the capital F abbreviates the franc; a lone "f" is too ambiguous."""
        assert normalize_currency_in_text("5 f") == "5 f"

    def test_unknown_currency_is_left_unchanged(self):
        assert normalize_currency_in_text("5 000 naira") == "5 000 naira"


class TestNumericExpressionsWithCurrency:
    def test_currency_is_off_by_default_so_existing_output_is_unchanged(self):
        assert normalize_numeric_expressions("A ye 5 000 FCFA sara.") == (
            "A ye waa duuru FCFA sara."
        )

    def test_currency_enabled(self):
        assert normalize_numeric_expressions("A ye 5 000 FCFA ni 3 sara.", currency=True) == (
            "A ye sefa wari waa kelen ni saba sara."
        )

    def test_currency_without_numbers_leaves_bare_numbers(self):
        result = normalize_numeric_expressions(
            "A ye 5 000 FCFA ni 3 sara.", currency=True, numbers=False
        )
        assert result == "A ye sefa wari waa kelen ni 3 sara."

    def test_currency_then_numbers_matches_both_at_once(self):
        """Enabled currency shields its amount, so numbers expanded later do not re-read it."""
        text = "A ye 5 000 FCFA ni 3 sara."
        currency_first = normalize_numeric_expressions(text, currency=True, numbers=False)

        result = normalize_numeric_expressions(currency_first)

        assert result == normalize_numeric_expressions(text, currency=True)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [("$20.5", "dolari wari mugan tomi duuru"), ("$2 000", "dolari wari waa fila")],
    )
    def test_prefixed_amount_with_decimal_or_grouping(self, text, expected):
        assert normalize_numeric_expressions(text, currency=True) == expected

    def test_arithmetic_keeps_precedence_over_currency(self):
        """A complete operation is read as one; the currency after it stays as written."""
        assert normalize_numeric_expressions("5-3 FCFA", currency=True) == "saba bɔ duuru la FCFA"

    def test_currency_and_measurement_side_by_side(self):
        assert normalize_numeric_expressions("malo 25 kg 5 000 FCFA", currency=True) == (
            "malo kilogaramu mugan ni duuru sefa wari waa kelen"
        )

    def test_date_keeps_precedence_over_currency(self):
        assert normalize_numeric_expressions("24-12-2025 F", currency=True) == (
            "Desanburu kalo tile mugan ni naani san baa fila ni mugan ni duuru F"
        )

    def test_currency_takes_precedence_over_number(self):
        spans = find_numeric_spans("A ye 5 000 FCFA ni 3 sara", currency=True)
        assert [(s.source, s.kind) for s in spans] == [
            ("5 000 FCFA", "currency"),
            ("3", "number"),
        ]

    def test_span_classification_ignores_currency_unless_asked(self):
        spans = find_numeric_spans("A ye 5 000 FCFA sara")
        assert [(s.source, s.kind) for s in spans] == [("5 000", "number")]


class TestNormalizerConfig:
    def test_expand_currency_option(self):
        config = BambaraNormalizerConfig(expand_currency=True, expand_numbers=True)
        assert (
            BambaraNormalizer(config)("A ye 100 000 FCFA sara") == "a ye sefa wari waa mugan sara"
        )

    def test_expand_currency_is_off_by_default(self):
        assert BambaraNormalizerConfig().expand_currency is False

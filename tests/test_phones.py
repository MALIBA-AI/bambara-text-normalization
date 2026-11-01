"""Phone number normalization tests."""

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    find_numeric_spans,
    normalize_numeric_expressions,
    normalize_phone_numbers_in_text,
    phone_number_to_bambara,
)

SPOKEN_76_12_34_56 = "bi wolonwula ni wɔɔrɔ, tan ni fila, bi saba ni naani, bi duuru ni wɔɔrɔ"
SPOKEN_COUNTRY_CODE = "kɛmɛ fila ni mugan ni saba"
UNBROKEN_76123456 = (
    "miliyɔn bi wolonwula ni wɔɔrɔ ni waa kɛmɛ ni mugan ni saba ni kɛmɛ naani ni bi duuru ni wɔɔrɔ"
)


class TestEveryFormatReadsTheSame:
    """
    A Malian number is written in many ways. The reading must not depend on which one
    the writer chose (issue #32).
    """

    @pytest.mark.parametrize(
        "written",
        ["76 12 34 56", "76-12-34-56", "76.12.34.56", "76 12 34 56"],
    )
    def test_pairs_with_a_separator(self, written):
        """
        Four pairs that share one separator are a phone number without a country code.
        """
        assert normalize_numeric_expressions(written) == SPOKEN_76_12_34_56

    @pytest.mark.parametrize(
        "written",
        [
            "+223 76 12 34 56",
            "+223 76-12-34-56",
            "+223 76123456",
            "+22376123456",
            "00223 76 12 34 56",
            "+223 76 123 456",
        ],
    )
    def test_with_the_country_code(self, written):
        """
        After +223 or 00223, eight digits are a phone number in any grouping,
        unbroken or grouped 2-3-3.
        """
        assert (
            normalize_numeric_expressions(written) == f"{SPOKEN_COUNTRY_CODE}, {SPOKEN_76_12_34_56}"
        )


class TestPhoneNumberToBambara:
    def test_a_pair_starting_with_zero_is_said_digit_by_digit(self):
        """Read as a number, "06" would lose its zero."""
        assert phone_number_to_bambara("20 06 11 00") == "mugan, fu wɔɔrɔ, tan ni kelen, fu fu"

    def test_not_a_phone_number_raises(self):
        with pytest.raises(ValueError):
            phone_number_to_bambara("12 345 678")


class TestNotAPhoneNumber:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                "12345678",
                "miliyɔn tan ni fila ni waa kɛmɛ saba ni bi naani ni duuru ni kɛmɛ wɔɔrɔ "
                "ni bi wolonwula ni seegin",
            ),
            (
                "12 345 678",
                "miliyɔn tan ni fila ni waa kɛmɛ saba ni bi naani ni duuru ni kɛmɛ wɔɔrɔ "
                "ni bi wolonwula ni seegin",
            ),
            ("76 123 456", UNBROKEN_76123456),
            ("76123456", UNBROKEN_76123456),
            ("50000000", "miliyɔn bi duuru"),
            ("A ye 30000000 sɔrɔ", "A ye miliyɔn bi saba sɔrɔ"),
        ],
    )
    def test_an_amount_stays_a_number(self, text, expected):
        """
        Without a country code, eight unbroken digits are an amount, like digits
        grouped by three as thousands; only separated pairs make a phone number.
        """
        assert normalize_numeric_expressions(text) == expected

    @pytest.mark.parametrize("currency", [True, False])
    def test_an_amount_with_its_currency_is_not_a_phone_number(self, currency):
        """
        A currency after the digits makes them an amount, whether or not currency
        expansion is turned on.
        """
        spans = find_numeric_spans("76 12 34 56 FCFA", currency=currency)

        assert not [span for span in spans if span.kind == "phone"]

    @pytest.mark.parametrize(
        "text", ["76 12 34 56 FCFA", "76 12 34 56 F", "20 30 40 50 kg", "$76 12 34 56"]
    )
    def test_a_currency_or_unit_next_to_the_digits_rules_out_a_phone(self, text):
        """
        A currency or measurement unit before or after the digits means they count
        something, so they are never read as a phone number.
        """
        assert not [span for span in find_numeric_spans(text) if span.kind == "phone"]

    def test_a_date_stays_a_date(self):
        assert (
            normalize_numeric_expressions("24-12-2025")
            == "Desanburu tile mugan ni naani san baa fila ni mugan ni duuru"
        )

    @pytest.mark.parametrize(
        "text",
        ["76 12 34 56 78", "76-12 34.56", "7612345678", "a76123456", "+33 76 12 34 56"],
    )
    def test_other_shapes_are_not_read_as_a_malian_number(self, text):
        """
        A fifth pair, mixed separators, ten digits, a glued letter or another country
        code: none is an eight-digit Malian number.
        """
        assert not [span for span in find_numeric_spans(text) if span.kind == "phone"]


class TestInText:
    def test_two_numbers_in_one_sentence(self):
        assert normalize_phone_numbers_in_text("76.12.34.56, 20 06 11 00.") == (
            f"{SPOKEN_76_12_34_56}, mugan, fu wɔɔrɔ, tan ni kelen, fu fu."
        )

    def test_disabled_phones_are_left_alone_and_not_read_as_numbers(self):
        """A disabled kind shields its digits, like every other kind."""
        assert normalize_numeric_expressions("76 12 34 56", phones=False) == "76 12 34 56"

    def test_the_normalizer_reads_phones_when_it_expands_numbers(self):
        """The normalizer's default config also strips the pauses' commas."""
        normalizer = BambaraNormalizer(BambaraNormalizerConfig(expand_numbers=True))

        expected = SPOKEN_76_12_34_56.replace(",", "")
        assert normalizer.normalize("76 12 34 56") == expected

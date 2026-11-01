import pytest

from bambara_normalizer import (
    bambara_to_number,
    denormalize_numbers_in_text,
    normalize,
    normalize_numbers_in_text,
    normalize_numeric_expressions,
    number_to_bambara,
)


class TestNumberToBambara:
    def test_units(self):
        assert number_to_bambara(0) == "fu"
        assert number_to_bambara(1) == "kelen"
        assert number_to_bambara(5) == "duuru"
        assert number_to_bambara(9) == "kɔnɔntɔn"

    def test_tens(self):
        assert number_to_bambara(10) == "tan"
        assert number_to_bambara(15) == "tan ni duuru"
        assert number_to_bambara(20) == "mugan"
        assert number_to_bambara(25) == "mugan ni duuru"

    def test_hundreds(self):
        assert number_to_bambara(100) == "kɛmɛ"
        assert number_to_bambara(123) == "kɛmɛ ni mugan ni saba"
        assert number_to_bambara(200) == "kɛmɛ fila"
        assert number_to_bambara(500) == "kɛmɛ duuru"

    def test_thousands(self):
        assert number_to_bambara(1000) == "waa kelen"
        assert number_to_bambara(5000) == "waa duuru"
        assert number_to_bambara(10000) == "waa tan"

    def test_millions(self):
        assert number_to_bambara(1000000) == "miliyɔn kelen"

    def test_decimal(self):
        assert number_to_bambara(5.3) == "duuru tomi saba"


class TestBambaraToNumber:
    def test_units(self):
        assert bambara_to_number("fu") == 0
        assert bambara_to_number("kelen") == 1
        assert bambara_to_number("duuru") == 5

    def test_compound(self):
        assert bambara_to_number("tan ni duuru") == 15
        assert bambara_to_number("kɛmɛ ni mugan ni saba") == 123
        assert bambara_to_number("waa kelen") == 1000

    def test_decimal(self):
        assert bambara_to_number("duuru tomi saba") == 5.3


class TestNumberTextNormalization:
    def test_normalize_numbers_in_text(self):
        assert normalize_numbers_in_text("A ye 5 wari di") == "A ye duuru wari di"
        assert normalize_numbers_in_text("Mɔgɔ 100 nana") == "Mɔgɔ kɛmɛ nana"

    def test_denormalize_numbers_in_text(self):
        assert denormalize_numbers_in_text("A ye duuru wari di") == "A ye 5 wari di"
        assert denormalize_numbers_in_text("Mɔgɔ kɛmɛ nana") == "Mɔgɔ 100 nana"

    def test_trailing_punctuation_is_not_a_decimal_separator(self):
        assert normalize_numbers_in_text("Ne wolo la san 2020.") == (
            "Ne wolo la san waa fila ni mugan."
        )
        assert normalize_numbers_in_text("A ye 42, 43 di") == (
            "A ye bi naani ni fila, bi naani ni saba di"
        )

    def test_separator_between_digits_is_kept(self):
        assert normalize_numbers_in_text("A ye 3.5 di") == "A ye saba tomi duuru di"
        assert normalize_numbers_in_text("Mɔgɔ 1,000 nana") == "Mɔgɔ waa kelen nana"


class TestNumberNormalizerIntegration:
    def test_with_expand_numbers(self):
        result = normalize("A ye 5 wari di", expand_numbers=True)
        assert "duuru" in result
        assert "5" not in result

    def test_without_expand_numbers(self):
        result = normalize("A ye 5 wari di", expand_numbers=False)
        assert "5" in result
        assert "duuru" not in result

    def test_wer_preset_expands_numbers(self, wer_normalizer):
        result = wer_normalizer("A ye 100 sɔrɔ")
        assert "kɛmɛ" in result


class TestNumberRoundTrip:
    def test_round_trip_conversion(self):
        test_numbers = [0, 1, 5, 10, 15, 20, 42, 100, 123, 500, 1000, 5000]
        for n in test_numbers:
            bambara = number_to_bambara(n)
            back = bambara_to_number(bambara)
            assert back == n, f"Round trip failed for {n}: {bambara} -> {back}"


class TestSpaceGroupedThousands:
    """French typography groups thousands with a space, a no-break space or a narrow one."""

    def test_regular_space(self):
        assert normalize_numbers_in_text("Mɔgɔ 3 500 nana") == ("Mɔgɔ waa saba ni kɛmɛ duuru nana")

    def test_millions(self):
        assert normalize_numbers_in_text("1 000 000") == "miliyɔn kelen"
        assert normalize_numbers_in_text("2 500 000") == "miliyɔn fila ni waa kɛmɛ duuru"

    @pytest.mark.parametrize("separator", [" ", " "])
    def test_no_break_spaces(self, separator):
        assert normalize_numbers_in_text(f"12{separator}500") == "waa tan ni fila ni kɛmɛ duuru"

    def test_number_to_bambara_accepts_grouped_string(self):
        assert number_to_bambara("1 000 000") == "miliyɔn kelen"

    def test_groups_must_be_three_digits(self):
        assert normalize_numbers_in_text("tile 1 2 3") == "tile kelen fila saba"
        assert normalize_numbers_in_text("san 2020 100 mɔgɔ") == ("san waa fila ni mugan kɛmɛ mɔgɔ")


class TestDecimalComma:
    """A comma followed by anything but exactly three digits cannot be a thousands group."""

    def test_one_decimal_digit(self):
        assert normalize_numbers_in_text("A ye 2,5 di") == "A ye fila tomi duuru di"

    def test_two_decimal_digits(self):
        assert number_to_bambara("12,75") == "tan ni fila tomi wolonwula duuru"

    def test_three_digits_stay_a_thousands_group(self):
        assert normalize_numbers_in_text("Mɔgɔ 1,500 nana") == ("Mɔgɔ waa kelen ni kɛmɛ duuru nana")
        assert number_to_bambara("1,000,000") == "miliyɔn kelen"


class TestMillionWord:
    def test_spelling(self):
        assert number_to_bambara(2_000_000) == "miliyɔn fila"

    def test_round_trip(self):
        for n in [1_000_000, 2_500_000, 7_000_005]:
            assert bambara_to_number(number_to_bambara(n)) == n


class TestGroupedThousandsWithDecimal:
    """With space grouping the comma can only be the decimal separator, whatever follows it."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1 000,5", "waa kelen tomi duuru"),
            ("1 000.5", "waa kelen tomi duuru"),
            ("1 000,500", "waa kelen tomi duuru"),
        ],
    )
    def test_grouped_integer_keeps_its_fraction(self, text, expected):
        assert normalize_numbers_in_text(text) == expected
        assert number_to_bambara(text) == expected

    def test_common_round_thousands(self):
        assert normalize_numbers_in_text("12 000") == "waa tan ni fila"
        assert normalize_numbers_in_text("20 000") == "waa mugan"

    @pytest.mark.parametrize("text", ["1 2 3", "12 34", "1 00"])
    def test_malformed_grouping_is_still_rejected(self, text):
        with pytest.raises(ValueError):
            number_to_bambara(text)


class TestDotThousandsSeparator:
    """A single dot before exactly three digits groups thousands, mirroring the comma: "1.000 FCFA"."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1.000", "waa kelen"),
            ("3.500", "waa saba ni kɛmɛ duuru"),
            ("1.234", "waa kelen ni kɛmɛ fila ni bi saba ni naani"),
        ],
    )
    def test_three_digits_after_the_dot(self, text, expected):
        assert normalize_numbers_in_text(text) == expected
        assert number_to_bambara(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("3.5", "saba tomi duuru"),
            ("12.25", "tan ni fila tomi fila duuru"),
            ("3.1415", "saba tomi kelen naani kelen duuru"),
        ],
    )
    def test_other_lengths_stay_decimal(self, text, expected):
        assert number_to_bambara(text) == expected

    def test_dot_grouped_operand_in_arithmetic(self):
        assert normalize_numeric_expressions("1.000 + 1") == "waa kelen fara kelen kan"


class TestPercent:
    """A numeral directly, or across a space of any kind, before `%` reads as percent."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("50%", "bi duuru kɛmɛsarada"),
            ("50 %", "bi duuru kɛmɛsarada"),
            ("50  %", "bi duuru kɛmɛsarada"),
            ("50     %", "bi duuru kɛmɛsarada"),
            ("50 %", "bi duuru kɛmɛsarada"),
            ("50 %", "bi duuru kɛmɛsarada"),
        ],
    )
    def test_whole_number(self, text, expected):
        assert normalize_numbers_in_text(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("12,5%", "tan ni fila tomi duuru kɛmɛsarada"),
            ("12,5 %", "tan ni fila tomi duuru kɛmɛsarada"),
            ("12,5  %", "tan ni fila tomi duuru kɛmɛsarada"),
            ("12,5    %", "tan ni fila tomi duuru kɛmɛsarada"),
            ("12,5 %", "tan ni fila tomi duuru kɛmɛsarada"),
            ("12,5 %", "tan ni fila tomi duuru kɛmɛsarada"),
        ],
    )
    def test_decimal(self, text, expected):
        assert normalize_numbers_in_text(text) == expected

    def test_percent_sign_is_consumed(self):
        assert "%" not in normalize_numbers_in_text("A ye 50% sɔrɔ")

    def test_in_sentence(self):
        assert normalize_numbers_in_text("A ye 50 % sɔrɔ") == "A ye bi duuru kɛmɛsarada sɔrɔ"
class TestOrdinalNumbers:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1er", "fɔlɔ"),
            ("1ère", "fɔlɔ"),
            ("1re", "fɔlɔ"),
            ("2e", "filanan"),
            ("2è", "filanan"),
            ("2ème", "filanan"),
            ("2eme", "filanan"),
            ("3ième", "sabanan"),
            ("2nd", "filanan"),
            ("2nde", "filanan"),
            ("5nan", "duurunan"),
            ("10e", "tannan"),
            ("21e", "mugan ni kelennan"),
        ],
    )
    def test_ordinal_suffix_is_read_as_bambara_ordinal(self, text, expected):
        """
        A numeral carrying a French ordinal suffix (er, e, ème, nd...) or the
        Bambara suffix "nan" is read with the Bambara ordinal: "fɔlɔ" for one,
        the cardinal followed by "nan" otherwise.
        """
        result = normalize_numeric_expressions(text)

        assert result == expected

    def test_ordinal_inside_a_sentence(self):
        """
        The ordinal is replaced in place and the surrounding words are kept.
        """
        text = "A sera 2e ye, n tun ye 1er ye"

        result = normalize_numeric_expressions(text)

        assert result == "A sera filanan ye, n tun ye fɔlɔ ye"

    def test_suffix_is_case_insensitive(self):
        """
        Upper-case suffixes, as in headings, are read the same way.
        """
        assert normalize_numeric_expressions("1ER 2E") == "fɔlɔ filanan"

    @pytest.mark.parametrize("text", ["2em", "2 e", "2emploi", "2,5e"])
    def test_numeral_followed_by_other_letters_is_not_an_ordinal(self, text):
        """
        Only a suffix that ends the word makes an ordinal. A numeral glued to a
        longer word, or separated from the suffix by a space, keeps its
        cardinal reading.
        """
        result = normalize_numeric_expressions(text)

        assert result.startswith("fila")
        assert "filanan" not in result

    def test_normalize_numbers_in_text_reads_ordinals(self):
        """
        The number-only entry point gives the same ordinal reading.
        """
        assert normalize_numbers_in_text("2e") == "filanan"

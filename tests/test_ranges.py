"""Range normalization tests."""

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    normalize_numeric_expressions,
    normalize_ranges_in_text,
)


class TestTimeRanges:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("8h-10h", "Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan"),
            ("8h - 10h", "Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan"),
            ("8h–10h", "Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan"),
            ("14:00-16:00", "Nɛgɛ kanɲɛ tan ni naani fo Nɛgɛ kanɲɛ tan ni wɔɔrɔ"),
            ("9h-12h30", "Nɛgɛ kanɲɛ kɔnɔntɔn fo Nɛgɛ kanɲɛ tan ni fila ni sanga bi saba"),
        ],
    )
    def test_two_times_joined_by_a_dash_are_a_range(self, text, expected):
        """Times are not subtracted, so the dash between two of them is always "until"."""
        assert normalize_numeric_expressions(text) == expected

    def test_each_end_keeps_its_own_reading(self):
        """The range only joins its ends; a time is said as it would be alone."""
        alone = normalize_numeric_expressions("10h30")

        assert normalize_numeric_expressions("10h30-12h").startswith(f"{alone} fo ")


class TestYearRanges:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("2020-2025", "waa fila ni mugan fo waa fila ni mugan ni duuru"),
            ("2020 - 2025", "waa fila ni mugan fo waa fila ni mugan ni duuru"),
            ("2026–2027", "waa fila ni mugan ni wɔɔrɔ fo waa fila ni mugan ni wolonwula"),
        ],
    )
    def test_two_increasing_years_are_a_range(self, text, expected):
        """
        Two increasing years are a period even with spaces around the dash, where
        "2020 - 2025" used to read as a subtraction.
        """
        assert normalize_numeric_expressions(text) == expected


class TestNotARange:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("3-1", "kelen bɔ saba la"),
            ("8 - 5", "duuru bɔ seegin na"),
            ("2025 - 2020", "waa fila ni mugan bɔ waa fila ni mugan ni duuru la"),
        ],
    )
    def test_a_dash_between_plain_numbers_keeps_its_reading(self, text, expected):
        """
        Between plain numbers, or years that do not increase, the dash may be a minus
        sign. The text does not say, so nothing changes.
        """
        assert normalize_numeric_expressions(text) == expected

    def test_a_date_keeps_its_year(self):
        """The year of a date is not the start of a year range."""
        assert normalize_numeric_expressions("12-05-2024-2025").startswith(
            "Mɛ kalo tile tan ni fila san baa fila ni mugan ni naani"
        )


class TestNumberRanges:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("5-10", "duuru fo tan"),
            ("(5-10 san)", "(duuru fo tan san)"),
            ("tile 20-25", "tile mugan fo mugan ni duuru"),
            ("kilo 240-250", "kilo kɛmɛ fila ni bi naani fo kɛmɛ fila ni bi duuru"),
            ("0-5", "fu fo duuru"),
            ("5–10", "duuru fo tan"),
        ],
    )
    def test_a_tight_dash_between_increasing_numbers_is_a_range(self, text, expected):
        """
        "5-10" written with no spaces and a larger second number is how an interval
        is written; a subtraction giving a negative number is not.
        """
        assert normalize_numeric_expressions(text) == expected

    @pytest.mark.parametrize(
        ("text", "alone"),
        [
            ("5-10 kg", "5 kg"),
            ("15-20 minutes", "15 minutes"),
            ("8-10h", "8h"),
        ],
    )
    def test_a_unit_after_the_second_end_is_said_on_both_ends(self, text, alone):
        """
        The unit written once after the range belongs to both ends, as in time
        ranges where each end keeps its full reading.
        """
        first = normalize_numeric_expressions(alone)

        result = normalize_numeric_expressions(text)

        assert result.startswith(f"{first} fo ")
        assert not any(character.isdigit() for character in result)

    def test_a_currency_after_the_second_end_is_said_on_both_ends(self):
        """
        Only when currency is enabled, like any other money amount.
        """
        first = normalize_numeric_expressions("1000 FCFA", currency=True)
        last = normalize_numeric_expressions("2000 FCFA", currency=True)

        result = normalize_numeric_expressions("1000-2000 FCFA", currency=True)

        assert result == f"{first} fo {last}"

    def test_a_currency_before_the_first_end_is_said_on_both_ends(self):
        """
        "FCFA 1000-2000" is the same range with the currency written first.
        """
        expected = normalize_numeric_expressions("1000-2000 FCFA", currency=True)

        assert normalize_numeric_expressions("FCFA 1000-2000", currency=True) == expected

    @pytest.mark.parametrize(
        "text",
        ["15-15-15", "20-22-33-44", "2011-087", "12-2025", "1,5-2", "5-10abc"],
    )
    def test_chains_leading_zeros_and_mixed_shapes_are_not_number_ranges(self, text):
        """
        A chain is a code or a phone number, a leading zero marks a reference
        number, and a year beside a small number is a date fragment.
        """
        assert " fo " not in normalize_numeric_expressions(text)

    def test_a_spaced_dash_keeps_its_subtraction_reading(self):
        """
        "5 - 10" is written like an operation, so the convention leaves it one.
        """
        assert normalize_numeric_expressions("5 - 10") == "tan bɔ duuru la"


class TestInText:
    def test_ranges_in_a_sentence(self):
        assert normalize_ranges_in_text("Butiki bɛ dayɛlɛ 8h-17h.") == (
            "Butiki bɛ dayɛlɛ Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan ni wolonwula."
        )

    def test_disabled_ranges_are_left_alone(self):
        """A disabled kind shields its text, like every other kind."""
        assert normalize_numeric_expressions("8h-10h", ranges=False) == "8h-10h"

    def test_the_normalizer_reads_ranges_when_it_expands_times(self):
        normalizer = BambaraNormalizer(BambaraNormalizerConfig(expand_times=True))

        assert normalizer.normalize("8h-10h") == "nɛgɛ kanɲɛ seegin fo nɛgɛ kanɲɛ tan"

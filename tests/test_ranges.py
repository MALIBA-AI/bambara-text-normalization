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
            ("8h-10h", "lɛrɛ seegin fo lɛrɛ tan"),
            ("8h - 10h", "lɛrɛ seegin fo lɛrɛ tan"),
            ("8h–10h", "lɛrɛ seegin fo lɛrɛ tan"),
            ("14:00-16:00", "Nɛgɛ kaɲɛ tan ni naani fo Nɛgɛ kaɲɛ tan ni wɔɔrɔ"),
            ("9h-12h30", "lɛrɛ kɔnɔntɔn fo Nɛgɛ kaɲɛ tan ni fila ni sanga bi saba"),
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
            "Mɛ tile tan ni fila san baa fila ni mugan ni naani"
        )


class TestInText:
    def test_ranges_in_a_sentence(self):
        assert normalize_ranges_in_text("Butiki bɛ da wuli 8h-17h, san 2020-2025 kɔnɔ.") == (
            "Butiki bɛ da wuli lɛrɛ seegin fo lɛrɛ tan ni wolonwula, "
            "san waa fila ni mugan fo waa fila ni mugan ni duuru kɔnɔ."
        )

    def test_disabled_ranges_are_left_alone(self):
        """A disabled kind shields its text, like every other kind."""
        assert normalize_numeric_expressions("8h-10h", ranges=False) == "8h-10h"

    def test_the_normalizer_reads_ranges_when_it_expands_times(self):
        normalizer = BambaraNormalizer(BambaraNormalizerConfig(expand_times=True))

        assert normalizer.normalize("8h-10h") == "lɛrɛ seegin fo lɛrɛ tan"

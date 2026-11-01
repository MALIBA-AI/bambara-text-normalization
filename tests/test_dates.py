from datetime import date

import pytest

from bambara_normalizer import (
    DAYS_OF_WEEK,
    MONTHS,
    bambara_to_date,
    bambara_to_day_of_week,
    bambara_to_month,
    date_to_bambara,
    day_of_week_to_bambara,
    format_date_bambara,
    is_bambara_day,
    is_bambara_month,
    month_to_bambara,
    normalize,
    normalize_dates_in_text,
    normalize_numeric_expressions,
)


class TestDateToBambara:
    def test_basic(self):
        result = date_to_bambara(2024, 10, 13)
        assert "Oktɔburu" in result
        assert "tile" in result
        assert "tan ni saba" in result
        assert "san" in result

    def test_january(self):
        result = date_to_bambara(2008, 1, 25)
        assert "Zanwuye" in result
        assert "mugan ni duuru" in result

    def test_with_kalo(self):
        result = date_to_bambara(2024, 10, 13, include_kalo=True)
        assert "kalo" in result

    def test_with_day_of_week(self):
        result = date_to_bambara(2024, 10, 13, include_day_of_week=True)
        assert "Kari" in result

    def test_uses_ba_for_year(self):
        result = date_to_bambara(2024, 10, 13)
        assert "baa fila" in result


class TestBambaraToDate:
    def test_basic(self):
        bambara = "Oktɔburu tile tan ni saba san baa fila ni mugan ni naani"
        result = bambara_to_date(bambara)
        assert result.year == 2024
        assert result.month == 10
        assert result.day == 13

    def test_january(self):
        bambara = "Zanwuye tile mugan ni duuru san baa fila ni seegin"
        result = bambara_to_date(bambara)
        assert result.month == 1
        assert result.day == 25
        assert result.year == 2008


class TestFormatDateBambara:
    def test_from_date_object(self):
        d = date(2024, 10, 13)
        result = format_date_bambara(d)
        assert "Oktɔburu" in result

    def test_from_string_french(self):
        result = format_date_bambara("13-10-2024")
        assert "Oktɔburu" in result
        assert "tan ni saba" in result

    def test_from_string_iso(self):
        result = format_date_bambara("2024-10-13")
        assert "Oktɔburu" in result


class TestDayOfWeek:
    def test_to_bambara(self):
        assert day_of_week_to_bambara(0) == "Tɛnɛn"
        assert day_of_week_to_bambara(4) == "Juma"
        assert day_of_week_to_bambara(6) == "Kari"

    def test_from_bambara(self):
        assert bambara_to_day_of_week("Tɛnɛn") == 0
        assert bambara_to_day_of_week("Juma") == 4
        assert bambara_to_day_of_week("Kari") == 6


class TestMonth:
    def test_to_bambara(self):
        assert month_to_bambara(1) == "Zanwuye"
        assert month_to_bambara(5) == "Mɛ"
        assert month_to_bambara(10) == "Oktɔburu"
        assert month_to_bambara(12) == "Desanburu"

    def test_from_bambara(self):
        assert bambara_to_month("Zanwuye") == 1
        assert bambara_to_month("Mɛ") == 5
        assert bambara_to_month("Oktɔburu") == 10


class TestDateTextNormalization:
    def test_french_format(self):
        text = "A bɛ na 13-10-2024 la"
        result = normalize_dates_in_text(text)
        assert "Oktɔburu" in result
        assert "13-10-2024" not in result

    def test_iso_format(self):
        text = "A bɛ na 2024-10-13 la"
        result = normalize_dates_in_text(text)
        assert "Oktɔburu" in result

    def test_multiple_dates(self):
        text = "13-10-2024 fo 25-01-2025"
        result = normalize_dates_in_text(text)
        assert "Oktɔburu" in result
        assert "Zanwuye" in result


class TestDateCheckers:
    def test_is_bambara_month(self):
        assert is_bambara_month("Oktɔburu") is True
        assert is_bambara_month("oktɔburu") is True
        assert is_bambara_month("October") is False

    def test_is_bambara_day(self):
        assert is_bambara_day("Juma") is True
        assert is_bambara_day("juma") is True
        assert is_bambara_day("Friday") is False


class TestDateConstants:
    def test_all_months_defined(self):
        assert len(MONTHS) == 12
        for i in range(1, 13):
            assert i in MONTHS

    def test_all_days_defined(self):
        assert len(DAYS_OF_WEEK) == 7
        for i in range(7):
            assert i in DAYS_OF_WEEK


class TestDateNormalizerIntegration:
    def test_with_expand_dates(self):
        result = normalize("A bɛ na 13-10-2024 la", expand_dates=True)
        assert "oktɔburu" in result
        assert "13-10-2024" not in result

    def test_without_expand_dates(self):
        result = normalize("A bɛ na 13-10-2024 la", expand_dates=False, remove_punctuation=False)
        assert "13-10-2024" in result
        assert "oktɔburu" not in result.lower()

    def test_wer_preset_expands_dates(self, wer_normalizer):
        result = wer_normalizer("A bɛ na 13-10-2024 la")
        assert "oktɔburu" in result


class TestDateRoundTrip:
    def test_single_date(self):
        original = date(2024, 10, 13)
        bambara = format_date_bambara(original)
        back = bambara_to_date(bambara)
        assert back == original

    def test_multiple_dates(self):
        dates = [
            date(2024, 1, 1),
            date(2024, 5, 15),
            date(2024, 12, 31),
            date(2000, 6, 20),
        ]
        for d in dates:
            bambara = format_date_bambara(d)
            back = bambara_to_date(bambara)
            assert back == d, f"Round trip failed for {d}: {bambara} -> {back}"


class TestDateValidation:
    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            date_to_bambara(2024, 13, 1)
        with pytest.raises(ValueError):
            date_to_bambara(2024, 0, 1)

    def test_invalid_day_raises(self):
        with pytest.raises(ValueError):
            date_to_bambara(2024, 10, 32)
        with pytest.raises(ValueError):
            date_to_bambara(2024, 10, 0)


class TestFrenchMonthNameDates:
    """
    A French date written with the month name ("1er janvier 2026") is read like any
    other date: month first, then the day, then the year said with "baa".
    """

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1er janvier 2026", "Zanwuye kalo tile fɔlɔ san baa fila ni mugan ni wɔɔrɔ"),
            ("1ère janvier 2026", "Zanwuye kalo tile fɔlɔ san baa fila ni mugan ni wɔɔrɔ"),
            ("15 mars 2025", "Marsi kalo tile tan ni duuru san baa fila ni mugan ni duuru"),
            ("2 août 2026", "Uti kalo tile fila san baa fila ni mugan ni wɔɔrɔ"),
            ("2 aout 2026", "Uti kalo tile fila san baa fila ni mugan ni wɔɔrɔ"),
            (
                "25 Décembre 2024",
                "Desanburu kalo tile mugan ni duuru san baa fila ni mugan ni naani",
            ),
            ("3 FÉVRIER 2026", "Feburuye kalo tile saba san baa fila ni mugan ni wɔɔrɔ"),
        ],
    )
    def test_day_month_name_and_year(self, text, expected):
        """
        The month name moves before the day, and "1er" reads as the ordinal "fɔlɔ".
        """
        result = normalize_numeric_expressions(text, include_kalo=True)

        assert result == expected

    def test_day_and_month_without_a_year(self):
        """
        A date with no year is read without one.
        """
        result = normalize_numeric_expressions("A bɛ na 1er janvier la", include_kalo=True)

        assert result == "A bɛ na Zanwuye kalo tile fɔlɔ la"

    def test_kalo_follows_the_caller_setting(self):
        """
        The month word follows include_kalo like the numeric date formats.
        """
        result = normalize_numeric_expressions("15 mars 2025", include_kalo=False)

        assert result == "Marsi tile tan ni duuru san baa fila ni mugan ni duuru"

    @pytest.mark.parametrize("text", ["31 février 2026", "30 février", "32 mars 2026"])
    def test_impossible_date_is_not_a_date(self, text):
        """
        A day the month does not have is not read as a date.
        """
        assert normalize_dates_in_text(text) == text

    def test_ordinal_suffix_only_for_the_first(self):
        """
        Only the first of the month is written "1er"; "2er janvier" is not a date.
        """
        assert normalize_dates_in_text("2er janvier 2026") == "2er janvier 2026"

    def test_month_name_inside_a_word_is_not_a_month(self):
        """
        The month must be a whole word: "3 marsupiaux" is no date.
        """
        assert normalize_dates_in_text("3 marsupiaux") == "3 marsupiaux"

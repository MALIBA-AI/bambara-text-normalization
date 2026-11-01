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


class TestMonthWordKalo:
    """
    A date names the month with "kalo" after the month name ("Mɛ kalo"), the way
    it is said; the word is on unless a caller turns it off.
    """

    def test_date_in_text_names_the_month_with_kalo(self):
        """
        A written date reads with "kalo" by default.
        """
        result = normalize_numeric_expressions("12/05/2026")

        assert result == "Mɛ kalo tile tan ni fila san baa fila ni mugan ni wɔɔrɔ"

    def test_date_to_bambara_includes_kalo_by_default(self):
        """
        The date function says "kalo" without being asked.
        """
        result = date_to_bambara(2024, 10, 13)

        assert result == "Oktɔburu kalo tile tan ni saba san baa fila ni mugan ni naani"

    def test_normalizer_reads_dates_with_kalo(self):
        """
        The full normalizer gives the same reading.
        """
        result = normalize("12/05/2026", expand_dates=True)

        assert result == "mɛ kalo tile tan ni fila san baa fila ni mugan ni wɔɔrɔ"

    def test_kalo_can_still_be_turned_off(self):
        """
        Callers that do not want the month word can still leave it out.
        """
        result = normalize_numeric_expressions("12/05/2026", include_kalo=False)

        assert result == "Mɛ tile tan ni fila san baa fila ni mugan ni wɔɔrɔ"

    def test_date_with_kalo_parses_back(self):
        """
        A date read with "kalo" converts back to the same date.
        """
        assert bambara_to_date(date_to_bambara(2026, 5, 12)) == date(2026, 5, 12)

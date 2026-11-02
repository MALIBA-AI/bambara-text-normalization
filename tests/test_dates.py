from datetime import date

import pytest

from bambara_normalizer import (
    DAYS_OF_WEEK,
    MONTHS,
    BambaraNormalizer,
    BambaraNormalizerConfig,
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

    @pytest.mark.parametrize("text", ["1 janvier 2026", "01/01/2026", "2026-01-01"])
    def test_first_of_the_month_is_always_folo(self, text):
        """
        The first day of a month is said "tile fɔlɔ" however it is written:
        "1er janvier", "1 janvier" or "01/01".
        """
        result = normalize_numeric_expressions(text, include_kalo=True)

        assert result == "Zanwuye kalo tile fɔlɔ san baa fila ni mugan ni wɔɔrɔ"

    def test_date_on_the_first_parses_back(self):
        """
        "tile fɔlɔ" converts back to day 1.
        """
        assert bambara_to_date(date_to_bambara(2026, 1, 1, include_kalo=True)) == date(2026, 1, 1)

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


class TestKaloSetting:
    """
    "kalo" can be turned on or off from the normalizer configuration, like the
    other expansion settings.
    """

    def test_normalizer_says_kalo_by_default(self):
        """
        The default configuration says the month word.
        """
        normalizer = BambaraNormalizer(BambaraNormalizerConfig(expand_dates=True))

        assert normalizer.normalize("1er janvier 2026") == (
            "zanwuye kalo tile fɔlɔ san baa fila ni mugan ni wɔɔrɔ"
        )

    def test_normalizer_can_leave_kalo_out(self):
        """
        include_kalo=False drops the month word from every date.
        """
        config = BambaraNormalizerConfig(expand_dates=True, include_kalo=False)

        result = BambaraNormalizer(config).normalize("1er janvier 2026 ni 12/05/2026")

        assert result == (
            "zanwuye tile fɔlɔ san baa fila ni mugan ni wɔɔrɔ "
            "ni mɛ tile tan ni fila san baa fila ni mugan ni wɔɔrɔ"
        )

    def test_normalize_function_accepts_the_setting(self):
        """
        The one-call normalize() takes the same setting.
        """
        result = normalize("12/05/2026", expand_dates=True, include_kalo=False)

        assert result == "mɛ tile tan ni fila san baa fila ni mugan ni wɔɔrɔ"


class TestYearAfterSan:
    """
    A year written after "san" (year) is said with "baa", like the year of a full
    date (issue #43).
    """

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("san 2026", "san baa fila ni mugan ni wɔɔrɔ"),
            ("San 1998", "San baa kelen ni kɛmɛ kɔnɔntɔn ni bi kɔnɔntɔn ni seegin"),
            ("SAN 2026", "SAN baa fila ni mugan ni wɔɔrɔ"),
            ("A bɛ na san 2026 la", "A bɛ na san baa fila ni mugan ni wɔɔrɔ la"),
            ("san 2026 kɔnɔ", "san baa fila ni mugan ni wɔɔrɔ kɔnɔ"),
        ],
    )
    def test_year_after_san_uses_baa(self, text, expected):
        """
        "san" followed by a four-digit year reads the year with "baa", in any case.
        """
        assert normalize_numeric_expressions(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("2026", "waa fila ni mugan ni wɔɔrɔ"),
            ("A ye 2026 FCFA di", "A ye waa fila ni mugan ni wɔɔrɔ FCFA di"),
            ("sanji 2026", "sanji waa fila ni mugan ni wɔɔrɔ"),
        ],
    )
    def test_number_without_san_is_unchanged(self, text, expected):
        """
        Without "san" right before it, a four-digit number stays a plain number.
        """
        assert normalize_numeric_expressions(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("A ye a san 2500 FCFA la", "A ye a san waa fila ni kɛmɛ duuru FCFA la"),
            ("san 0999", "san kɛmɛ kɔnɔntɔn ni bi kɔnɔntɔn ni kɔnɔntɔn"),
            ("san 26", "san mugan ni wɔɔrɔ"),
            ("san 20260", "san waa mugan ni kɛmɛ fila ni bi wɔɔrɔ"),
        ],
    )
    def test_amount_or_non_year_after_san_is_not_a_year(self, text, expected):
        """
        "san" is also the verb "buy": a currency after the digits makes them a price,
        and anything that is not a four-digit year from 1000 to 2999 stays a number.
        """
        assert normalize_numeric_expressions(text) == expected

    def test_year_range_after_san_is_left_to_the_range(self):
        """
        "san 2026-2027" is a range, so the year reading does not take its first year.
        """
        assert normalize_numeric_expressions("san 2026-2027") == (
            "san waa fila ni mugan ni wɔɔrɔ fo waa fila ni mugan ni wolonwula"
        )

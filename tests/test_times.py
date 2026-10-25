"""Time normalization tests."""

from datetime import time

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    bambara_to_duration,
    bambara_to_time,
    duration_to_bambara,
    format_duration_bambara,
    format_time_bambara,
    is_time_word,
    normalize,
    normalize_times_in_text,
    time_to_bambara,
)


class TestClockTimeToBambara:
    def test_whole_hour(self):
        result = time_to_bambara(1, 0)
        assert result == "Nɛgɛ kaɲɛ kelen"

    def test_with_minutes(self):
        result = time_to_bambara(1, 5)
        assert result == "Nɛgɛ kaɲɛ kelen ni sanga duuru"

    def test_7_30(self):
        result = time_to_bambara(7, 30)
        assert result == "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"

    def test_13_50(self):
        result = time_to_bambara(13, 50)
        assert result == "Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru"

    def test_midnight(self):
        result = time_to_bambara(0, 0)
        assert result == "Nɛgɛ kaɲɛ fu"

    def test_noon(self):
        result = time_to_bambara(12, 0)
        assert result == "Nɛgɛ kaɲɛ tan ni fila"

    def test_with_seconds(self):
        result = time_to_bambara(7, 30, 15)
        assert result == "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba ni segɔni tan ni duuru"


class TestBambaraToClockTime:
    def test_whole_hour(self):
        result = bambara_to_time("Nɛgɛ kaɲɛ kelen")
        assert result.hour == 1
        assert result.minute == 0

    def test_with_minutes(self):
        bambara = "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"
        result = bambara_to_time(bambara)
        assert result.hour == 7
        assert result.minute == 30

    def test_13_50(self):
        bambara = "Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru"
        result = bambara_to_time(bambara)
        assert result.hour == 13
        assert result.minute == 50

    def test_midnight(self):
        result = bambara_to_time("Nɛgɛ kaɲɛ fu")
        assert result.hour == 0
        assert result.minute == 0


class TestFormatTimeBambara:
    def test_from_string(self):
        result = format_time_bambara("7:30")
        assert result == "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"

    def test_from_time_object(self):
        t = time(7, 30)
        result = format_time_bambara(t)
        assert result == "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"

    def test_from_string_13_50(self):
        result = format_time_bambara("13:50")
        assert result == "Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru"


class TestDurationToBambara:
    def test_minutes_only(self):
        result = duration_to_bambara(minutes=30)
        assert result == "miniti bi saba"

    def test_hours_and_minutes(self):
        result = duration_to_bambara(hours=1, minutes=30)
        assert result == "lɛrɛ kelen ni miniti bi saba"

    def test_full(self):
        result = duration_to_bambara(hours=1, minutes=30, seconds=10)
        assert result == "lɛrɛ kelen ni miniti bi saba ni segɔni tan"

    def test_hours_only(self):
        result = duration_to_bambara(hours=2)
        assert result == "lɛrɛ fila"

    def test_seconds_only(self):
        result = duration_to_bambara(seconds=45)
        assert result == "segɔni bi naani ni duuru"


class TestBambaraToDuration:
    def test_minutes_only(self):
        result = bambara_to_duration("miniti bi saba")
        assert result == (0, 30, 0)

    def test_hours_and_minutes(self):
        result = bambara_to_duration("lɛrɛ kelen ni miniti bi saba")
        assert result == (1, 30, 0)

    def test_full(self):
        result = bambara_to_duration("lɛrɛ kelen ni miniti bi saba ni segɔni tan")
        assert result == (1, 30, 10)

    def test_hours_only(self):
        result = bambara_to_duration("lɛrɛ fila")
        assert result == (2, 0, 0)


class TestFormatDurationBambara:
    def test_30min(self):
        result = format_duration_bambara("30min")
        assert result == "miniti bi saba"

    def test_1h30min(self):
        result = format_duration_bambara("1h30min")
        assert result == "lɛrɛ kelen ni miniti bi saba"

    def test_1h30min10s(self):
        result = format_duration_bambara("1h30min10s")
        assert result == "lɛrɛ kelen ni miniti bi saba ni segɔni tan"


class TestTimeTextNormalization:
    def test_clock_time(self):
        text = "A nana 7:30 la"
        result = normalize_times_in_text(text)
        assert result == "A nana Nɛgɛ kaɲɛ wolonwula ni sanga bi saba la"

    def test_duration(self):
        text = "A tagara 1h30min"
        result = normalize_times_in_text(text)
        assert result == "A tagara lɛrɛ kelen ni miniti bi saba"

    def test_multiple(self):
        text = "A nana 7:30 wa a tagara 30min kɔfɛ"
        result = normalize_times_in_text(text)
        assert "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba" in result
        assert "miniti bi saba" in result


class TestIsTimeWord:
    def test_time_words(self):
        assert is_time_word("lɛrɛ") is True
        assert is_time_word("miniti") is True
        assert is_time_word("segɔni") is True
        assert is_time_word("sanga") is True

    def test_non_time_word(self):
        assert is_time_word("taa") is False


class TestTimeNormalizerIntegration:
    def test_with_expand_times(self):
        result = normalize("A nana 7:30 la", expand_times=True)
        assert "nɛgɛ kaɲɛ wolonwula ni sanga bi saba" in result
        assert "7:30" not in result

    def test_without_expand_times(self):
        result = normalize("A nana 7:30 la", expand_times=False, remove_punctuation=False)
        assert "7:30" in result

    def test_wer_preset_expands_times(self):
        config = BambaraNormalizerConfig.for_wer_evaluation()
        normalizer = BambaraNormalizer(config)
        result = normalizer("A nana 7:30 la")
        assert "nɛgɛ kaɲɛ" in result


class TestTimeRoundTrip:
    def test_clock_time(self):
        original = time(7, 30)
        bambara = format_time_bambara(original)
        back = bambara_to_time(bambara)
        assert back.hour == original.hour
        assert back.minute == original.minute

    def test_clock_time_13_50(self):
        original = time(13, 50)
        bambara = format_time_bambara(original)
        back = bambara_to_time(bambara)
        assert back.hour == original.hour
        assert back.minute == original.minute

    def test_duration(self):
        original = (1, 30, 10)
        bambara = duration_to_bambara(*original)
        back = bambara_to_duration(bambara)
        assert back == original

    def test_multiple_times(self):
        times = [time(0, 0), time(1, 5), time(7, 30), time(12, 0), time(13, 50), time(23, 59)]
        for t in times:
            bambara = format_time_bambara(t)
            back = bambara_to_time(bambara)
            assert back.hour == t.hour, f"Hour mismatch for {t}: {bambara}"
            assert back.minute == t.minute, f"Minute mismatch for {t}: {bambara}"


class TestTimeValidation:
    def test_invalid_hour_raises(self):
        with pytest.raises(ValueError):
            time_to_bambara(25, 0)

    def test_invalid_minute_raises(self):
        with pytest.raises(ValueError):
            time_to_bambara(1, 60)

    def test_invalid_second_raises(self):
        with pytest.raises(ValueError):
            time_to_bambara(1, 30, 60)

    def test_invalid_phrase_raises(self):
        with pytest.raises(ValueError):
            bambara_to_time("invalid time phrase")


class TestFrenchClockTime:
    """French writes clock times with an "h" between hour and minutes: 10h30, 14h05."""

    def test_in_sentence(self):
        assert normalize_times_in_text("A bɛ na 10h30 la") == (
            "A bɛ na Nɛgɛ kaɲɛ tan ni sanga bi saba la"
        )

    def test_uppercase_and_leading_zero_minutes(self):
        assert normalize_times_in_text("14H05") == "Nɛgɛ kaɲɛ tan ni naani ni sanga duuru"

    def test_bare_hour_stays_a_duration(self):
        assert normalize_times_in_text("10h") == "lɛrɛ tan"

    def test_duration_with_minute_unit_is_unchanged(self):
        assert normalize_times_in_text("1h30min") == "lɛrɛ kelen ni miniti bi saba"

    @pytest.mark.parametrize("text", ["25h30", "10h75"])
    def test_impossible_clock_time_is_not_a_time(self, text):
        assert normalize_times_in_text(text) == text

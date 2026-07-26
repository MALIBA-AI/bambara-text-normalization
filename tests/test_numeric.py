"""Order-independence tests for the unified numeric pass."""

import itertools

import pytest

from bambara_normalizer import (
    KIND_PRECEDENCE,
    BambaraNormalizer,
    BambaraNormalizerConfig,
    find_numeric_spans,
    normalize_numeric_expressions,
)

MIXED_TEXT = "Ne taara sugu la 24-12-2025 la, 10:45 waati, ne ye tulu 6 l san ani sukaro 10 kg."

FLAG_FOR_KIND = {
    "date": "dates",
    "time": "times",
    "measurement": "measurements",
    "number": "numbers",
}


def only(kind):
    """Flags enabling a single kind."""
    return {flag: (k == kind) for k, flag in FLAG_FOR_KIND.items()}


class TestSpanClassification:
    def test_each_numeric_span_is_claimed_once(self):
        spans = find_numeric_spans(MIXED_TEXT)
        assert [(s.source, s.kind) for s in spans] == [
            ("24-12-2025", "date"),
            ("10:45", "time"),
            ("6 l", "measurement"),
            ("10 kg", "measurement"),
        ]

    def test_spans_do_not_overlap(self):
        spans = find_numeric_spans("13/10/2024 ni 7:30:15 ani 2.5 L ani 42 ani 1h30min")
        for previous, current in zip(spans, spans[1:]):
            assert previous.end <= current.start

    def test_bare_number_kept_as_number(self):
        spans = find_numeric_spans("A ye 42 di")
        assert [(s.source, s.kind) for s in spans] == [("42", "number")]

    def test_unexpandable_date_falls_through_to_number(self):
        # 45-13-2025 is not a date, so it must not reserve the span.
        spans = find_numeric_spans("A bɛ 45-13-2025 la")
        assert {s.kind for s in spans} == {"number"}


class TestOrderIndependence:
    @pytest.mark.parametrize("order", list(itertools.permutations(KIND_PRECEDENCE)))
    def test_expanding_one_kind_at_a_time_is_order_independent(self, order):
        expected = normalize_numeric_expressions(MIXED_TEXT)

        result = MIXED_TEXT
        for kind in order:
            result = normalize_numeric_expressions(result, **only(kind))

        assert result == expected

    @pytest.mark.parametrize("order", list(itertools.permutations(KIND_PRECEDENCE)))
    def test_order_independent_on_ambiguous_shapes(self, order):
        text = "1h30min, 2024-01-05, 100 m, 3,5 kg, 7:05, 12"
        expected = normalize_numeric_expressions(text)

        result = text
        for kind in order:
            result = normalize_numeric_expressions(result, **only(kind))

        assert result == expected

    def test_repeated_expansion_is_idempotent(self):
        once = normalize_numeric_expressions(MIXED_TEXT)
        assert normalize_numeric_expressions(once) == once


class TestPartialConfigGuards:
    def test_disabled_dates_are_not_expanded_as_numbers(self):
        assert normalize_numeric_expressions("A bɛ 24-12-2025 la", dates=False) == (
            "A bɛ 24-12-2025 la"
        )

    def test_disabled_times_are_not_expanded_as_numbers(self):
        assert normalize_numeric_expressions("A nana 10:45 la", times=False) == "A nana 10:45 la"

    def test_disabled_measurements_are_not_expanded_as_numbers(self):
        assert normalize_numeric_expressions("A ye 6 l san", measurements=False) == "A ye 6 l san"

    def test_disabled_kind_still_lets_others_through(self):
        result = normalize_numeric_expressions("A bɛ 24-12-2025 la ni 3", dates=False)
        assert result == "A bɛ 24-12-2025 la ni saba"

    def test_all_disabled_leaves_text_untouched(self):
        assert (
            normalize_numeric_expressions(
                MIXED_TEXT, dates=False, times=False, measurements=False, numbers=False
            )
            == MIXED_TEXT
        )


class TestNormalizerIntegration:
    def test_wer_preset_expands_every_kind(self):
        normalizer = BambaraNormalizer(BambaraNormalizerConfig.for_wer_evaluation())
        result = normalizer(MIXED_TEXT)

        assert "desanburu" in result
        assert "nɛgɛ kaɲɛ" in result
        assert "litiri wɔɔrɔ" in result
        assert "kilogaramu tan" in result
        assert not any(char.isdigit() for char in result)

    def test_numbers_only_config_protects_other_kinds(self):
        config = BambaraNormalizerConfig(
            expand_numbers=True,
            expand_dates=False,
            expand_times=False,
            expand_measurements=False,
            remove_punctuation=False,
        )
        result = BambaraNormalizer(config)(MIXED_TEXT)

        assert "24-12-2025" in result
        assert "10:45" in result
        assert "6 l" in result

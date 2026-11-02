"""Order-independence tests for the unified numeric pass."""

import random

import pytest

from bambara_normalizer import (
    KIND_PRECEDENCE,
    BambaraNormalizer,
    BambaraNormalizerConfig,
    find_numeric_spans,
    normalize_numeric_expressions,
)

MIXED_TEXT = (
    "Ne taara sugu la 24-12-2025 la, 10:45 waati, ne ye tulu 6 l san ani sukaro 10 kg, "
    "wari 12 + 8 = 20."
)

RANGES_AND_PHONES_TEXT = (
    "San 2020-2025, butiki bɛ dayɛlɛ 8h-17h30, telefɔni 76 12 34 56 walima +223 66123456, "
    "3 kg, 12 - 5 = 7, 1er janvier 2026, 25%"
)

FLAG_FOR_KIND = {
    "date": "dates",
    "range": "ranges",
    "time": "times",
    "arithmetic": "arithmetic",
    "currency": "currency",
    "phone": "phones",
    "measurement": "measurements",
    "number": "numbers",
}

SHUFFLED_ORDERINGS = 48


def sample_orderings(kinds, shuffles=SHUFFLED_ORDERINGS, seed=0):
    """
    A fixed, reproducible sample of orderings of the expander kinds.

    Checking all n! orderings grows too fast (40 320 for 8 kinds), and an ordering bug
    shows up in almost any reordering. The sample keeps the orderings most likely to
    expose one: the declared order and its reverse, every rotation of both (each kind
    runs first and last), every swap of two neighbouring kinds (each precedence pair
    inverted), and seeded shuffles for everything else.
    """
    kinds = tuple(kinds)
    reverse = kinds[::-1]
    orderings = [kinds, reverse]
    for base in (kinds, reverse):
        orderings += [base[i:] + base[:i] for i in range(1, len(base))]
    for i in range(len(kinds) - 1):
        swapped = list(kinds)
        swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        orderings.append(tuple(swapped))
    generator = random.Random(seed)
    for _ in range(shuffles):
        shuffled = list(kinds)
        generator.shuffle(shuffled)
        orderings.append(tuple(shuffled))
    return list(dict.fromkeys(orderings))


ORDERINGS = sample_orderings(KIND_PRECEDENCE)


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
            ("12 + 8 = 20", "arithmetic"),
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
    def test_every_kind_has_a_flag(self):
        """
        Each kind must be switchable on its own, or the orderings below never move it.
        """
        assert set(FLAG_FOR_KIND) == set(KIND_PRECEDENCE)

    def test_sample_is_reproducible_and_covers_every_kind_first_and_last(self):
        """
        The sample is the same on every run, and every kind runs first and runs last
        in at least one ordering.
        """
        assert sample_orderings(KIND_PRECEDENCE) == ORDERINGS
        assert {order[0] for order in ORDERINGS} == set(KIND_PRECEDENCE)
        assert {order[-1] for order in ORDERINGS} == set(KIND_PRECEDENCE)

    @pytest.mark.parametrize("order", ORDERINGS)
    def test_expanding_one_kind_at_a_time_is_order_independent(self, order):
        expected = normalize_numeric_expressions(MIXED_TEXT)

        result = MIXED_TEXT
        for kind in order:
            result = normalize_numeric_expressions(result, **only(kind))

        assert result == expected

    @pytest.mark.parametrize("order", ORDERINGS)
    def test_order_independent_on_ambiguous_shapes(self, order):
        text = "1h30min, 2024-01-05, 100 m, 3,5 kg, 7:05, 12"
        expected = normalize_numeric_expressions(text)

        result = text
        for kind in order:
            result = normalize_numeric_expressions(result, **only(kind))

        assert result == expected

    @pytest.mark.parametrize("order", ORDERINGS)
    def test_order_independent_with_ranges_and_phones(self, order):
        """
        Year and time ranges and phone numbers give the same text whatever order the
        kinds are expanded in.
        """
        expected = normalize_numeric_expressions(RANGES_AND_PHONES_TEXT)

        result = RANGES_AND_PHONES_TEXT
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

    def test_disabled_arithmetic_is_not_expanded_as_numbers(self):
        assert normalize_numeric_expressions("A ko 2 + 2", arithmetic=False) == "A ko 2 + 2"

    def test_disabled_kind_still_lets_others_through(self):
        result = normalize_numeric_expressions("A bɛ 24-12-2025 la ni 3", dates=False)
        assert result == "A bɛ 24-12-2025 la ni saba"

    def test_all_disabled_leaves_text_untouched(self):
        assert (
            normalize_numeric_expressions(
                MIXED_TEXT,
                dates=False,
                times=False,
                arithmetic=False,
                measurements=False,
                numbers=False,
            )
            == MIXED_TEXT
        )


class TestNormalizerIntegration:
    def test_wer_preset_expands_every_kind(self):
        normalizer = BambaraNormalizer(BambaraNormalizerConfig.for_wer_evaluation())
        result = normalizer(MIXED_TEXT)

        assert "desanburu" in result
        assert "nɛgɛ kanɲɛ" in result
        assert "litiri wɔɔrɔ" in result
        assert "kilogaramu tan" in result
        assert "tan ni fila fara seegin kan" in result
        assert not any(char.isdigit() for char in result)

    def test_numbers_only_config_protects_other_kinds(self):
        config = BambaraNormalizerConfig(
            expand_numbers=True,
            expand_dates=False,
            expand_times=False,
            expand_arithmetic=False,
            expand_measurements=False,
            remove_punctuation=False,
        )
        result = BambaraNormalizer(config)(MIXED_TEXT)

        assert "24-12-2025" in result
        assert "10:45" in result
        assert "6 l" in result
        assert "12 + 8 = 20" in result


class TestWrittenNumberFormats:
    def test_grouped_operand_in_arithmetic(self):
        assert normalize_numeric_expressions("1 000 + 500") == ("waa kelen fara kɛmɛ duuru kan")

    def test_mixed_sentence(self):
        assert normalize_numeric_expressions("A bɛ na 10h30 la, 3 500 ani 2,5 kg") == (
            "A bɛ na Nɛgɛ kanɲɛ tan ni sanga bi saba la, waa saba ni kɛmɛ duuru ani "
            "kilogaramu fila tomi duuru"
        )

    def test_grouped_decimal_measurement_leaves_no_digit(self):
        assert normalize_numeric_expressions("A ye 2 500,75 kg") == (
            "A ye kilogaramu waa fila ni kɛmɛ duuru tomi wolonwula duuru"
        )

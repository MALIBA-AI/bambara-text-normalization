"""Span resolution tests."""

import random

import pytest

from bambara_normalizer.spans import KIND_PRECEDENCE, NumericSpan, _precedence_key, resolve_spans


def resolve_by_checking_every_accepted_span(candidates):
    """
    The plain definition of resolution: take candidates by precedence and keep one
    unless it overlaps any span already kept.
    """
    accepted = []
    for candidate in sorted(candidates, key=_precedence_key):
        if any(candidate.overlaps(span) for span in accepted):
            continue
        accepted.append(candidate)
    return sorted(accepted, key=lambda span: span.start)


def random_candidates(generator, count, text_length):
    candidates = []
    for _ in range(count):
        start = generator.randrange(text_length)
        end = min(text_length, start + generator.randint(1, 12))
        candidates.append(
            NumericSpan(
                start=start,
                end=end,
                kind=generator.choice(KIND_PRECEDENCE),
                source="x" * (end - start),
                replacement="y",
                tier=generator.randint(0, 2),
            )
        )
    return candidates


class TestResolveSpans:
    @pytest.mark.parametrize("seed", range(300))
    def test_matches_the_plain_definition(self, seed):
        """
        On random overlapping candidates, resolution keeps exactly the spans the
        plain definition keeps, in the same order.
        """
        generator = random.Random(seed)
        candidates = random_candidates(generator, count=generator.randint(0, 60), text_length=80)

        result = resolve_spans(candidates)

        assert result == resolve_by_checking_every_accepted_span(candidates)

    def test_touching_spans_are_both_kept(self):
        """
        A span ending where the next one starts does not overlap it.
        """
        first = NumericSpan(start=0, end=3, kind="number", source="abc", replacement="1")
        second = NumericSpan(start=3, end=5, kind="number", source="de", replacement="2")

        assert resolve_spans([second, first]) == [first, second]

    def test_higher_precedence_wins_an_overlap(self):
        """
        Of two overlapping spans, the one of the more specific kind is kept.
        """
        date = NumericSpan(start=0, end=10, kind="date", source="x" * 10, replacement="d")
        number = NumericSpan(start=3, end=5, kind="number", source="xx", replacement="n")

        assert resolve_spans([number, date]) == [date]

# Copyright 2026 sudoping01.

# Licensed under the MIT License; you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:

# https://opensource.org/licenses/MIT

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Range normalization for Bambara.

A dash between two times, two years or two increasing numbers is a range, read
with "fo" (until) between the two ends:

    8h-10h       ->  Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan
    14:00-16:00  ->  Nɛgɛ kanɲɛ tan ni naani fo Nɛgɛ kanɲɛ tan ni wɔɔrɔ
    2020-2025    ->  waa fila ni mugan fo waa fila ni mugan ni duuru
    5-10         ->  duuru fo tan
    5-10 kg      ->  kilogaramu duuru fo kilogaramu tan

Times are not subtracted, and two increasing years ("2020 - 2025") are a period even
with spaces around the dash. Between two plain numbers the convention is written,
not guessed: a dash with no spaces and a larger second number ("5-10") is an
interval, the way prices, ages and doses are written; anything else ("3-1",
"5 - 10") keeps the reading the other expanders give it. Chains ("15-15-15"), a
leading zero ("2011-087", a reference number) and a year beside a small number
("12-2025") are not number ranges.

Each end keeps the reading its own expander gives it, so a range never changes how a
time is said. A unit or currency written once, after the second end or before the
first, belongs to both ends and is said on each.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .arithmetic import YEAR_RANGE
from .currency import find_currency_spans
from .measurements import find_measurement_spans
from .numbers import number_to_bambara
from .spans import (
    RANGE,
    NumericSpan,
    _precedence_key,
    find_spans,
    resolve_spans,
    substitute,
)
from .times import find_time_spans

FO = "fo"

# A hyphen, an en dash or an em dash, with or without spaces around it.
RANGE_DASH_PATTERN = re.compile(r"\s*[-–—]\s*")

YEAR_RANGE_PATTERN = re.compile(r"(?<![\d.,/:-])(\d{4})\s*[-–—]\s*(\d{4})(?![\d.,/:-]?\d)")

# Two integers joined by a dash with no spaces. Neither end may be part of a longer
# number, a decimal or a chain, and only "0" itself may start with a zero.
NUMBER_RANGE_PATTERN = re.compile(
    r"(?<![\w.,/:–—-])(?P<first>0|[1-9]\d*)[-–](?P<last>[1-9]\d*)(?![\d.,/:]?\d)(?![-–—]\d)"
)

# Finders whose span may start at the second end ("10 kg", "20 minutes", "10h",
# "2000 FCFA") or end at the first ("FCFA 1000") and so carry the unit of the range.
SpanFinder = Callable[[str], list[NumericSpan]]


def find_range_spans(text: str, currency: bool = False) -> list[NumericSpan]:
    """
    Find time, year and number ranges in text and their Bambara expansions.

    A range wins over the times and numbers it is made of, and over the subtraction a
    dash would otherwise be read as.

    Args:
        text: Input text
        currency: Also carry a currency written next to a number range to both ends
    """
    return (
        _time_ranges(text)
        + find_spans(text, YEAR_RANGE_PATTERN, RANGE, _replace_year_range)
        + _number_ranges(text, currency)
    )


def _number_ranges(text: str, currency: bool) -> list[NumericSpan]:
    matches = [
        match
        for match in NUMBER_RANGE_PATTERN.finditer(text)
        if int(match.group("first")) < int(match.group("last"))
    ]
    if not matches:
        return []

    finders: list[SpanFinder] = [find_time_spans, find_measurement_spans]
    if currency:
        finders.append(find_currency_spans)
    unit_spans = [(finder, span) for finder in finders for span in finder(text)]

    spans = []
    for match in matches:
        span = _carry_unit(text, match, unit_spans) or _bare_number_range(text, match)
        if span is not None:
            spans.append(span)
    return spans


def _carry_unit(
    text: str, match: re.Match, unit_spans: list[tuple[SpanFinder, NumericSpan]]
) -> NumericSpan | None:
    """
    Read a number range whose unit is written once, on one end only.

    The bare end is re-read with the unit of the other one, by the same finder, so
    each end is said exactly as it would be on its own.
    """
    first, last = match.group("first"), match.group("last")
    first_start, last_end = match.start("first"), match.end("last")

    after = [
        (finder, span)
        for finder, span in unit_spans
        if span.start == match.start("last") and span.end > last_end
    ]
    before = [
        (finder, span)
        for finder, span in unit_spans
        if span.end == match.end("first") and span.start < first_start
    ]

    for finder, span in sorted(after, key=lambda pair: _precedence_key(pair[1])):
        bare_end = _read_whole(finder, first + text[last_end : span.end])
        if bare_end is not None:
            return _range_span(text, first_start, span.end, bare_end, span.replacement)

    for finder, span in sorted(before, key=lambda pair: _precedence_key(pair[1])):
        bare_end = _read_whole(finder, text[span.start : first_start] + last)
        if bare_end is not None:
            return _range_span(text, span.start, last_end, span.replacement, bare_end)

    return None


def _read_whole(finder: SpanFinder, source: str) -> str | None:
    for span in finder(source):
        if span.start == 0 and span.end == len(source):
            return span.replacement
    return None


def _bare_number_range(text: str, match: re.Match) -> NumericSpan | None:
    if match.end() < len(text) and text[match.end()].isalpha():
        return None

    first, last = int(match.group("first")), int(match.group("last"))
    is_year = [
        len(match.group(end)) == 4 and value in YEAR_RANGE
        for end, value in (("first", first), ("last", last))
    ]
    if is_year[0] != is_year[1]:
        return None

    return _range_span(
        text, match.start(), match.end(), number_to_bambara(first), number_to_bambara(last)
    )


def _range_span(text: str, start: int, end: int, first: str, last: str) -> NumericSpan:
    return NumericSpan(
        start=start,
        end=end,
        kind=RANGE,
        source=text[start:end],
        replacement=f"{first} {FO} {last}",
    )


def _time_ranges(text: str) -> list[NumericSpan]:
    times = resolve_spans(find_time_spans(text))
    spans = []

    for start, end in zip(times, times[1:]):
        if not RANGE_DASH_PATTERN.fullmatch(text[start.end : end.start]):
            continue

        spans.append(
            NumericSpan(
                start=start.start,
                end=end.end,
                kind=RANGE,
                source=text[start.start : end.end],
                replacement=f"{start.replacement} {FO} {end.replacement}",
            )
        )

    return spans


def _replace_year_range(match: re.Match) -> str | None:
    first, last = int(match.group(1)), int(match.group(2))
    if first not in YEAR_RANGE or last not in YEAR_RANGE or first >= last:
        return None
    return f"{number_to_bambara(first)} {FO} {number_to_bambara(last)}"


def normalize_ranges_in_text(text: str) -> str:
    """
    Replace time ranges and year ranges in text with Bambara.

    Args:
        text: Input text with ranges

    Returns:
        Text with each range read as its two ends joined by "fo"

    Examples:
        >>> normalize_ranges_in_text("Butiki bɛ dayɛlɛ 8h-17h")
        'Butiki bɛ dayɛlɛ Nɛgɛ kanɲɛ seegin fo Nɛgɛ kanɲɛ tan ni wolonwula'

        >>> normalize_ranges_in_text("2020-2025")
        'waa fila ni mugan fo waa fila ni mugan ni duuru'
    """
    return substitute(text, find_range_spans(text))

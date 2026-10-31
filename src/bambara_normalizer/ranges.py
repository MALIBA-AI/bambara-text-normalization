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

A dash between two times or two years is a range, read with "fo" (until) between
the two ends:

    8h-10h       ->  lɛrɛ seegin fo lɛrɛ tan
    14:00-16:00  ->  Nɛgɛ kaɲɛ tan ni naani fo Nɛgɛ kaɲɛ tan ni wɔɔrɔ
    2020-2025    ->  waa fila ni mugan fo waa fila ni mugan ni duuru

Only these two shapes are read as ranges, because only there the dash cannot be a
minus sign: times are not subtracted, and two increasing years ("2020 - 2025") are a
period even with spaces around the dash. Between two plain numbers the dash is left
to the other expanders: "3-1" may be a score, a range or an operation, and the text
alone does not say which.

Each end keeps the reading its own expander gives it, so a range never changes how a
time is said.
"""

from __future__ import annotations

import re

from .arithmetic import YEAR_RANGE
from .numbers import number_to_bambara
from .spans import RANGE, NumericSpan, find_spans, resolve_spans, substitute
from .times import find_time_spans

FO = "fo"

# A hyphen, an en dash or an em dash, with or without spaces around it.
RANGE_DASH_PATTERN = re.compile(r"\s*[-–—]\s*")

YEAR_RANGE_PATTERN = re.compile(r"(?<![\d.,/:-])(\d{4})\s*[-–—]\s*(\d{4})(?![\d.,/:-]?\d)")


def find_range_spans(text: str) -> list[NumericSpan]:
    """
    Find time ranges and year ranges in text and their Bambara expansions.

    A range wins over the times and numbers it is made of, and over the subtraction a
    spaced dash would otherwise be read as.
    """
    return _time_ranges(text) + find_spans(text, YEAR_RANGE_PATTERN, RANGE, _replace_year_range)


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
        >>> normalize_ranges_in_text("Butiki bɛ da wuli 8h-17h")
        'Butiki bɛ da wuli lɛrɛ seegin fo lɛrɛ tan ni wolonwula'

        >>> normalize_ranges_in_text("san 2020-2025 kɔnɔ")
        'san waa fila ni mugan fo waa fila ni mugan ni duuru kɔnɔ'
    """
    return substitute(text, find_range_spans(text))

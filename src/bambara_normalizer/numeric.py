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
Single-pass expansion of every numeric expression in a text.

Dates, times, measurements, and numbers are recognized in one classification
step, and each numeric span of the text is claimed by exactly one of them
(precedence: date > time > measurement > number). Only then is anything
rewritten, so the result never depends on the order the expanders are invoked in.

A span classified as a date is a date whether or not date expansion is enabled:
disabling `dates` leaves "24-12-2025" alone instead of letting the number
expander turn it into three unrelated numbers. Every partial combination of
flags is therefore safe, and applying the flags one at a time -- in any order --
gives the same text as applying them together.
"""

from __future__ import annotations

from .dates import find_date_spans
from .measurements import find_measurement_spans
from .numbers import find_number_spans
from .spans import (
    DATE,
    KIND_PRECEDENCE,
    MEASUREMENT,
    NUMBER,
    TIME,
    NumericSpan,
    apply_spans,
    resolve_spans,
)
from .times import find_time_spans


def find_numeric_spans(text: str, include_kalo: bool = False) -> list[NumericSpan]:
    """
    Classify every numeric span in text, non-overlapping, ordered by position.

    Args:
        text: Input text
        include_kalo: Include "kalo" after month names in date expansions

    Returns:
        The winning spans, each carrying its kind and Bambara expansion

    Examples:
        >>> [(s.source, s.kind) for s in find_numeric_spans("10:45 la, 6 l ni 3")]
        [('10:45', 'time'), ('6 l', 'measurement'), ('3', 'number')]
    """
    return resolve_spans(_candidates(text, KIND_PRECEDENCE, include_kalo))


def normalize_numeric_expressions(
    text: str,
    dates: bool = True,
    times: bool = True,
    measurements: bool = True,
    numbers: bool = True,
    include_kalo: bool = False,
) -> str:
    """
    Expand numeric expressions to Bambara in a single order-independent pass.

    Args:
        text: Input text
        dates: Expand date spans
        times: Expand time and duration spans
        measurements: Expand measurement spans
        numbers: Expand bare numerals
        include_kalo: Include "kalo" after month names in date expansions

    Returns:
        Text with the enabled kinds expanded. Spans of a disabled kind are left
        untouched -- never re-read as another kind.

    Examples:
        >>> normalize_numeric_expressions("Ne ye tulu 6 l san 10:45")
        'Ne ye litiri wɔɔrɔ san Nɛgɛ kaɲɛ tan ni sanga bi naani ni duuru'

        >>> normalize_numeric_expressions("A bɛ 24-12-2025 la", dates=False)
        'A bɛ 24-12-2025 la'
    """
    enabled = {DATE: dates, TIME: times, MEASUREMENT: measurements, NUMBER: numbers}

    scanned = _kinds_to_scan(enabled)
    if not scanned:
        return text

    spans = resolve_spans(_candidates(text, scanned, include_kalo))
    return apply_spans(text, [span for span in spans if enabled[span.kind]])


def _kinds_to_scan(enabled: dict[str, bool]) -> tuple[str, ...]:
    """
    The kinds worth classifying: everything down to the least specific enabled one.

    A disabled kind still has to be recognized when a *less* specific kind is
    enabled, so that its digits are shielded from it. Nothing below the last
    enabled kind can shield anything, so it is skipped.
    """
    ranks = [rank for rank, kind in enumerate(KIND_PRECEDENCE) if enabled[kind]]
    if not ranks:
        return ()
    return KIND_PRECEDENCE[: max(ranks) + 1]


def _candidates(text: str, kinds: tuple[str, ...], include_kalo: bool) -> list[NumericSpan]:
    finders = {
        DATE: lambda: find_date_spans(text, include_kalo=include_kalo),
        TIME: lambda: find_time_spans(text),
        MEASUREMENT: lambda: find_measurement_spans(text),
        NUMBER: lambda: find_number_spans(text),
    }

    candidates: list[NumericSpan] = []
    for kind in kinds:
        candidates.extend(finders[kind]())
    return candidates

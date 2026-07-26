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
Span primitives shared by the numeric expanders.

Each expander (dates, times, measurements, numbers) recognizes numeric spans of
text and knows how to rewrite them in Bambara. Instead of rewriting the text in
place -- which makes the result depend on the order the expanders run in -- every
expander reports the spans it recognizes, and a single resolution step decides
which of the (possibly overlapping) candidates win.

Precedence is by kind, from most specific to most generic:

    date > time > measurement > number

Within one kind, candidates are ordered by tier (the order the expander's own
patterns would have run in), then left to right, longest first.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

DATE = "date"
TIME = "time"
MEASUREMENT = "measurement"
NUMBER = "number"

KIND_PRECEDENCE = (DATE, TIME, MEASUREMENT, NUMBER)

_KIND_RANK = {kind: rank for rank, kind in enumerate(KIND_PRECEDENCE)}


@dataclass(frozen=True)
class NumericSpan:
    """A recognized numeric span and its Bambara expansion.

    Attributes:
        start: Start offset in the source text
        end: End offset in the source text (exclusive)
        kind: One of DATE, TIME, MEASUREMENT, NUMBER
        source: The matched text
        replacement: The Bambara expansion of `source`
        tier: Tie-break among candidates of the same kind (lower wins)
    """

    start: int
    end: int
    kind: str
    source: str
    replacement: str
    tier: int = 0

    def overlaps(self, other: NumericSpan) -> bool:
        return self.start < other.end and other.start < self.end


def find_spans(
    text: str,
    pattern: re.Pattern,
    kind: str,
    replacer: Callable[[re.Match], str | None],
    tier: int = 0,
) -> list[NumericSpan]:
    """
    Collect candidate spans for one pattern.

    The replacer returns the Bambara expansion of a match, or None when the match
    is not actually expandable (an impossible date, an unknown unit, ...). Such
    candidates are dropped, so they neither block nor shadow other candidates.
    """
    spans = []
    for match in pattern.finditer(text):
        replacement = replacer(match)
        if replacement is None:
            continue
        spans.append(
            NumericSpan(
                start=match.start(),
                end=match.end(),
                kind=kind,
                source=match.group(0),
                replacement=replacement,
                tier=tier,
            )
        )
    return spans


def _precedence_key(span: NumericSpan) -> tuple[int, int, int, int]:
    return (
        _KIND_RANK.get(span.kind, len(KIND_PRECEDENCE)),
        span.tier,
        span.start,
        -(span.end - span.start),
    )


def resolve_spans(candidates: Iterable[NumericSpan]) -> list[NumericSpan]:
    """
    Reduce overlapping candidates to a non-overlapping set, ordered by position.

    A candidate is kept unless a higher-precedence one already claimed part of
    its text. This is what makes expansion order-independent: precedence is a
    property of the candidates, not of the sequence the expanders ran in.
    """
    accepted: list[NumericSpan] = []
    for candidate in sorted(candidates, key=_precedence_key):
        if any(candidate.overlaps(span) for span in accepted):
            continue
        accepted.append(candidate)

    accepted.sort(key=lambda span: span.start)
    return accepted


def apply_spans(text: str, spans: Iterable[NumericSpan]) -> str:
    """Rewrite `text`, substituting each span with its replacement."""
    pieces = []
    cursor = 0
    for span in sorted(spans, key=lambda span: span.start):
        if span.start < cursor:
            continue
        pieces.append(text[cursor : span.start])
        pieces.append(span.replacement)
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def substitute(text: str, candidates: Iterable[NumericSpan]) -> str:
    """Resolve overlapping candidates and apply the winners in one pass."""
    return apply_spans(text, resolve_spans(candidates))

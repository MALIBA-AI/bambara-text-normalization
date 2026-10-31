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
Phone number normalization for Bambara.

A Malian number has eight digits. It is written in pairs ("76 12 34 56", "76-12-34-56",
"76.12.34.56") or unbroken ("76123456"), with or without the country code ("+223",
"00223"). Every format is read the same way, pair by pair with a pause between pairs:

    76 12 34 56       ->  bi wolonwula ni wɔɔrɔ, tan ni fila, bi saba ni naani, bi duuru ni wɔɔrɔ
    +223 76 12 34 56  ->  kɛmɛ fila ni mugan ni saba, bi wolonwula ni wɔɔrɔ, ...

A pair starting with 0 is said digit by digit ("06" -> "fu wɔɔrɔ"): read as a number it
would lose its zero.

Only eight digits starting with 2 to 9, the first digits of the Malian numbering plan,
are a phone number, and the pairs must share one separator. That keeps an amount
("12345678", "76 123 456") and a date ("24-12-2025") out of it.
"""

from __future__ import annotations

import re

from .numbers import UNITS, number_to_bambara
from .spans import PHONE, NumericSpan, find_spans, substitute

PAIR_PAUSE = ", "

MALI_COUNTRY_CODE = "223"

# A space (plain or no-break), a dot or a hyphen. The pairs of one number share one.
_SEPARATOR = r"[ \u00a0\u202f.-]"

PHONE_PATTERN = re.compile(
    # Nothing chained on either side: no letter, no "+", and no further digit group.
    rf"(?<![\w+])(?<!\d{_SEPARATOR})"
    rf"(?:(?P<country>(?:\+|00){MALI_COUNTRY_CODE}){_SEPARATOR}?)?"
    rf"(?P<number>[2-9]\d(?:(?P<separator>{_SEPARATOR})\d\d(?:(?P=separator)\d\d){{2}}|\d{{6}}))"
    rf"(?!{_SEPARATOR}?\d)(?!\w)"
)


def phone_number_to_bambara(phone_number: str) -> str:
    """
    Convert a Malian phone number to Bambara, pair by pair.

    Args:
        phone_number: The number as written, e.g. "76 12 34 56", "+223 76123456"

    Returns:
        The country code, when written, then each pair, separated by pauses

    Raises:
        ValueError: If the text is not an eight-digit Malian phone number

    Examples:
        >>> phone_number_to_bambara("76-12-34-56")
        'bi wolonwula ni wɔɔrɔ, tan ni fila, bi saba ni naani, bi duuru ni wɔɔrɔ'

        >>> phone_number_to_bambara("+223 20 06 11 00")
        'kɛmɛ fila ni mugan ni saba, mugan, fu wɔɔrɔ, tan ni kelen, fu fu'
    """
    match = PHONE_PATTERN.fullmatch(phone_number.strip())
    if match is None:
        raise ValueError(f"Not a phone number: {phone_number}")

    return _spoken_phone_number(match)


def _spoken_phone_number(match: re.Match) -> str:
    digits = re.sub(r"\D", "", match.group("number"))
    pairs = [_pair_to_bambara(digits[start : start + 2]) for start in range(0, len(digits), 2)]

    if match.group("country"):
        pairs.insert(0, number_to_bambara(int(MALI_COUNTRY_CODE)))

    return PAIR_PAUSE.join(pairs)


def _pair_to_bambara(pair: str) -> str:
    if pair.startswith("0"):
        return " ".join(UNITS[int(digit)] for digit in pair)
    return number_to_bambara(int(pair))


def find_phone_spans(text: str) -> list[NumericSpan]:
    """
    Find Malian phone numbers in text and their Bambara expansions.

    A phone number loses against dates, times, operations and money amounts, so
    "76123456 FCFA" stays an amount, and wins over measurements and bare numbers, so its
    digits are never read as one large number.
    """
    return find_spans(text, PHONE_PATTERN, PHONE, _spoken_phone_number)


def normalize_phone_numbers_in_text(text: str) -> str:
    """
    Replace Malian phone numbers in text with Bambara.

    Args:
        text: Input text with phone numbers

    Returns:
        Text with phone numbers read pair by pair

    Examples:
        >>> normalize_phone_numbers_in_text("76.12.34.56")
        'bi wolonwula ni wɔɔrɔ, tan ni fila, bi saba ni naani, bi duuru ni wɔɔrɔ'
    """
    return substitute(text, find_phone_spans(text))

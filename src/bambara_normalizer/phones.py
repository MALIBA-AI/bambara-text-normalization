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

Only eight digits starting with 2 to 9, the first digits of the Malian numbering plan
(5 to 9 for mobiles, 2 to 4 for fixed lines), can be a phone number. Eight digits alone
can as well be an amount ("80000000" is eighty million or a number), so in running text
a phone number is recognized by convention, on how it is written:

    - after the country code ("+223", "00223"), in any grouping: unbroken ("+22376123456"),
      in pairs, or grouped 2-3-3 ("+223 76 123 456");
    - without it, only as four pairs sharing one separator ("76 12 34 56", "76-12-34-56",
      "76.12.34.56").

Eight unbroken digits ("76123456") and digits grouped by three ("76 123 456") without a
country code stay amounts, and so do digits next to a currency or a measurement unit
("76 12 34 56 FCFA", "$76 12 34 56", "20 30 40 50 kg"). `phone_number_to_bambara` is
called on a known phone number, so it accepts every grouping.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .currency import CURRENCY_TO_BAMBARA, PREFIX_CURRENCIES
from .measurements import UNIT_TO_BAMBARA, UNIT_WORDS_TO_BAMBARA
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
    rf"(?P<number>[2-9]\d(?:"
    rf"(?P<separator>{_SEPARATOR})\d\d(?:(?P=separator)\d\d){{2}}"
    rf"|(?P<thousands_separator>{_SEPARATOR})\d{{3}}(?P=thousands_separator)\d{{3}}"
    rf"|\d{{6}}))"
    rf"(?!{_SEPARATOR}?\d)(?!\w)"
)


def _alternation(words: Iterable[str]) -> str:
    return "|".join(re.escape(word) for word in sorted(words, key=len, reverse=True))


# A currency or unit written right after the digits, or a currency right before them,
# means the digits count something: they are an amount, not a phone number.
COUNTED_AFTER_PATTERN = re.compile(
    rf"\s*(?:{_alternation([*CURRENCY_TO_BAMBARA, *UNIT_TO_BAMBARA, *UNIT_WORDS_TO_BAMBARA])})"
    rf"(?!\w)",
    re.IGNORECASE,
)
COUNTED_BEFORE_PATTERN = re.compile(
    rf"(?<!\w)(?:{_alternation(PREFIX_CURRENCIES)})\s*$", re.IGNORECASE
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


def _is_written_as_a_phone_number(match: re.Match) -> bool:
    if match.group("country"):
        return True
    return match.group("separator") is not None


def _counts_something(match: re.Match) -> bool:
    text = match.string
    return bool(
        COUNTED_AFTER_PATTERN.match(text, match.end())
        or COUNTED_BEFORE_PATTERN.search(text[: match.start()])
    )


def _replace_phone_number_in_text(match: re.Match) -> str | None:
    if not _is_written_as_a_phone_number(match) or _counts_something(match):
        return None
    return _spoken_phone_number(match)


def find_phone_spans(text: str) -> list[NumericSpan]:
    """
    Find Malian phone numbers in text and their Bambara expansions.

    Only digits written as a phone number by the convention above are found; the rest
    are left to the other kinds. A phone number loses against dates, times, operations
    and money amounts, and wins over measurements and bare numbers, so its digits are
    never read as one large number.
    """
    return find_spans(text, PHONE_PATTERN, PHONE, _replace_phone_number_in_text)


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

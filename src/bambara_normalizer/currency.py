# Copyright 2026 sudoping01.

# Licensed under the MIT License; you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:

# https://opensource.org/licenses/MIT

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import annotations

import re
from decimal import Decimal

from .numbers import (
    CONNECTOR,
    GROUPED_THOUSANDS,
    MILLION,
    THOUSAND,
    number_to_bambara,
    parse_number,
)
from .spans import CURRENCY, NumericSpan, find_spans, substitute

# Each currency name is followed by "wari" (money), as it is spoken.
SEFA = "sefa wari"
ERO = "ero wari"
DOLARI = "dolari wari"
LIVURU = "livuru wari"

# Spoken Bambara counts CFA francs below a million in dɔrɔmɛ, the five-franc
# coin, while millions keep their face value. The dɔrɔmɛ count is said in three
# pieces: hundreds of thousands and the remaining thousands each take "waa", and
# the part below a thousand is joined with "ani". When that last part is under
# 1 000 FCFA (fewer than two hundred dɔrɔmɛ, "kɛmɛ fila") the coin is named:
#
#     601 000 FCFA   = 120 200 dɔrɔmɛ  -> "sefa wari waa kɛmɛ ni waa mugan ani kɛmɛ fila"
#     620 250 FCFA   = 124 050 dɔrɔmɛ  -> "... ni waa mugan ni naani ani dɔrɔmɛ bi duuru"
#     1 500 000 FCFA = 1 million + 100 000 dɔrɔmɛ -> "sefa wari miliyɔn kelen ni waa kɛmɛ"
#
# An amount written in dɔrɔmɛ is already counted and is read as is.
DOROME = "dɔrɔmɛ"
DOROME_IN_CFA = 5
DOROME_NAMED_BELOW = 200
CFA_FACE_VALUE_UNIT = 1_000_000
ANI = "ani"

# Keys are lowercase. The Bambara word comes before the amount, as for units of
# measurement ("kilogaramu duuru"). "livre" is left out: after a number it means
# books far more often than pounds.
CURRENCY_TO_BAMBARA = {
    "fcfa": SEFA,
    "f cfa": SEFA,
    "f.cfa": SEFA,
    "cfa": SEFA,
    "xof": SEFA,
    "f": SEFA,
    "franc": SEFA,
    "francs": SEFA,
    "franc cfa": SEFA,
    "francs cfa": SEFA,
    "€": ERO,
    "eur": ERO,
    "euro": ERO,
    "euros": ERO,
    "$": DOLARI,
    "usd": DOLARI,
    "dollar": DOLARI,
    "dollars": DOLARI,
    "£": LIVURU,
    "gbp": LIVURU,
    DOROME: DOROME,
}

# Symbols and ISO codes are also written before the amount: "$20", "EUR 15".
PREFIX_CURRENCIES = ("€", "$", "£", "eur", "usd", "gbp", "xof")


def currency_to_bambara(amount: int | float | str, currency: str) -> str:
    """
    Convert a money amount to Bambara.

    Args:
        amount: The amount, as a number or as written ("1 000", "15,50")
        currency: Currency symbol, ISO code or name (e.g. "FCFA", "$", "euros")

    Returns:
        Bambara currency word followed by the amount. CFA amounts below a
        million are counted in dɔrɔmɛ (divided by five); an amount that is not a
        multiple of five keeps its exact value as a decimal number of dɔrɔmɛ,
        never rounded.

    Raises:
        ValueError: If the currency is unknown or the amount is not a numeral

    Examples:
        >>> currency_to_bambara("20 000", "FCFA")
        'sefa wari waa naani'

        >>> currency_to_bambara("1 500 000", "FCFA")
        'sefa wari miliyɔn kelen ni waa kɛmɛ'

        >>> currency_to_bambara(20, "$")
        'dolari wari mugan'
    """
    word = CURRENCY_TO_BAMBARA.get(" ".join(currency.split()).lower())
    if word is None:
        raise ValueError(f"Unknown currency: {currency}")

    value = parse_number(amount) if isinstance(amount, str) else amount

    if word == SEFA:
        return f"{word} {_spoken_cfa(value)}"

    return f"{word} {number_to_bambara(value)}"


def _spoken_cfa(value: int | float) -> str:
    # Decimal keeps the division exact: 7 FCFA is 1.4 dɔrɔmɛ, not 1.4000000000000001.
    millions, below_million = divmod(Decimal(str(value)), CFA_FACE_VALUE_UNIT)
    dorome = below_million / DOROME_IN_CFA

    pieces = []
    if millions:
        pieces.append(f"{MILLION} {number_to_bambara(int(millions))}")

    if dorome != dorome.to_integral_value():
        pieces.append(_dorome_count(float(dorome)))
        return f" {CONNECTOR} ".join(pieces)

    thousands, below_thousand = divmod(int(dorome), 1000)
    hundreds_of_thousands, other_thousands = divmod(thousands, 100)
    if hundreds_of_thousands:
        pieces.append(f"{THOUSAND} {number_to_bambara(hundreds_of_thousands * 100)}")
    if other_thousands:
        pieces.append(f"{THOUSAND} {number_to_bambara(other_thousands)}")

    spoken = f" {CONNECTOR} ".join(pieces)
    if not below_thousand:
        return spoken or number_to_bambara(0)
    if not spoken:
        return _dorome_count(below_thousand)
    return f"{spoken} {ANI} {_dorome_count(below_thousand)}"


def _dorome_count(dorome: int | float) -> str:
    if dorome < DOROME_NAMED_BELOW:
        return f"{DOROME} {number_to_bambara(dorome)}"
    return number_to_bambara(dorome)


def _alternation(names: list[str] | tuple[str, ...]) -> str:
    # Longest first, so "francs cfa" wins over "francs" and "fcfa" over "f".
    ordered = sorted(names, key=len, reverse=True)
    return "|".join(re.escape(name).replace(r"\ ", r"[  ]") for name in ordered)


def _build_patterns() -> tuple[re.Pattern, re.Pattern]:
    amount = rf"(?P<amount>{GROUPED_THOUSANDS}|\d+(?:[.,]\d+)*)"
    space = r"[   ]*"

    # A lone lowercase "f" is too ambiguous to read as the franc; only "F" is.
    suffix_names = [name for name in CURRENCY_TO_BAMBARA if name != "f"]
    suffix_currency = rf"(?P<currency>{_alternation(suffix_names)}|(?-i:F))"
    prefix_currency = rf"(?P<currency>{_alternation(PREFIX_CURRENCIES)})"

    # Neither side may run into a word: "5 Fanta" is not five francs.
    suffix = rf"(?<![\w.,]){amount}{space}{suffix_currency}(?![^\W\d_])"
    prefix = rf"(?<![^\W\d_]){prefix_currency}{space}{amount}(?![\d.,]?\d)"

    return (
        re.compile(suffix, re.IGNORECASE),
        re.compile(prefix, re.IGNORECASE),
    )


SUFFIX_CURRENCY_PATTERN, PREFIX_CURRENCY_PATTERN = _build_patterns()


def find_currency_spans(text: str) -> list[NumericSpan]:
    """
    Find money amounts in text and their Bambara expansions.

    The amount and its currency form one span, so the currency word is placed
    before the amount and the amount is not read again as a bare number.
    Unknown currencies are not matched and fall through to the number expander.
    """

    def replace(match: re.Match) -> str | None:
        try:
            return currency_to_bambara(match.group("amount"), match.group("currency"))
        except ValueError:
            return None

    return find_spans(text, SUFFIX_CURRENCY_PATTERN, CURRENCY, replace) + find_spans(
        text, PREFIX_CURRENCY_PATTERN, CURRENCY, replace, tier=1
    )


def normalize_currency_in_text(text: str) -> str:
    """
    Replace money amounts in text with Bambara.

    Recognizes formats:
    - 5 000 FCFA, 5000F, 2 500 francs CFA, 500 dɔrɔmɛ
    - 20 $, $20, €15,50, £100, USD 20

    Args:
        text: Input text with money amounts

    Returns:
        Text with money amounts converted to Bambara

    Examples:
        >>> normalize_currency_in_text("A ye 100 000 FCFA sara.")
        'A ye sefa wari waa mugan sara.'

        >>> normalize_currency_in_text("$20")
        'dolari wari mugan'
    """
    return substitute(text, find_currency_spans(text))

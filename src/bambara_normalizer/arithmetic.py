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
Arithmetic expression normalization module.

Reads an operator the way it is spoken rather than the way it is written, so a
TTS voice does not have to guess at "+", "-", "x", "÷" and "=":

    2 + 2      ->  fila fara fila kan
    8 - 5      ->  duuru bɔ seegin na
    5 x 3      ->  duuru siɲɛ saba
    10 / 2     ->  tan tila fila la
    2 + 2 = 4  ->  fila fara fila kan, o ye naani ye

Subtraction and division close with the postposition `la`, which surfaces as
`na` after a nasal -- hence "seegin na" but "fila la".

Only complete two-operand expressions are recognized, optionally followed by
`= result`. Anything longer is left alone, which is what keeps phone numbers
("20-22-33-44") and ISO dates ("2024-01-05") out of the arithmetic reading.
"""

from __future__ import annotations

import re

from .numbers import NUMBER_PATTERN, number_to_bambara
from .spans import ARITHMETIC, NumericSpan, find_spans, substitute

FARA = "fara"
KAN = "kan"
BO = "bɔ"
SINYE = "siɲɛ"
TILA = "tila"

LA = "la"
NA = "na"

O_PRONOUN = "o"
YE = "ye"

PLUS = "+"
MINUS = "-"
TIMES = "×"
DIVIDE = "÷"
EQUALS = "="

OPERATOR_ALIASES = {
    "+": PLUS,
    "-": MINUS,
    "−": MINUS,
    "×": TIMES,
    "*": TIMES,
    "x": TIMES,
    "X": TIMES,
    "÷": DIVIDE,
    "/": DIVIDE,
    "=": EQUALS,
}

OPERATOR_TO_BAMBARA = {
    PLUS: FARA,
    MINUS: BO,
    TIMES: SINYE,
    DIVIDE: TILA,
}


NASAL_ENDINGS = ("n", "m", "ɲ", "ŋ")


YEAR_RANGE = range(1000, 3000)


def is_arithmetic_operator(symbol: str) -> bool:
    """
    Whether a symbol is read as an arithmetic operator.

    Examples:
        >>> is_arithmetic_operator("×")
        True
        >>> is_arithmetic_operator(":")
        False
    """
    return symbol in OPERATOR_ALIASES


def _postposition(after: str) -> str:
    return NA if after.rstrip().endswith(NASAL_ENDINGS) else LA


def arithmetic_to_bambara(
    left: int | float | str,
    operator: str,
    right: int | float | str,
    result: int | float | str | None = None,
) -> str:
    """
    Convert an arithmetic operation to Bambara words.

    Args:
        left: Left operand
        operator: One of + - × ÷ (or the aliases * x /)
        right: Right operand
        result: Value after "=", when the expression states one

    Returns:
        The spoken Bambara form of the operation

    Raises:
        ValueError: If the operator is not an arithmetic operator

    Examples:
        >>> arithmetic_to_bambara(2, "+", 2)
        'fila fara fila kan'
        >>> arithmetic_to_bambara(8, "-", 5)
        'duuru bɔ seegin na'
        >>> arithmetic_to_bambara(5, "×", 3)
        'duuru siɲɛ saba'
        >>> arithmetic_to_bambara(10, "/", 2)
        'tan tila fila la'
        >>> arithmetic_to_bambara(2, "+", 2, result=4)
        'fila fara fila kan, o ye naani ye'
    """
    symbol = OPERATOR_ALIASES.get(operator)
    if symbol is None or symbol == EQUALS:
        raise ValueError(f"Not an arithmetic operator: {operator}")

    left_word = number_to_bambara(left)
    right_word = number_to_bambara(right)

    if symbol == PLUS:
        phrase = f"{left_word} {FARA} {right_word} {KAN}"
    elif symbol == MINUS:
        phrase = f"{right_word} {BO} {left_word} {_postposition(left_word)}"
    elif symbol == TIMES:
        phrase = f"{left_word} {SINYE} {right_word}"
    else:
        phrase = f"{left_word} {TILA} {right_word} {_postposition(right_word)}"

    if result is None:
        return phrase

    return f"{phrase}, {O_PRONOUN} {YE} {number_to_bambara(result)} {YE}"


_OPERAND = NUMBER_PATTERN.pattern

_OPERATOR = rf"[{re.escape('+-−×*÷/=')}]|(?<=\s)[xX](?=\s)"

_SEPARATOR = rf"\s*(?:{_OPERATOR})\s*"


ARITHMETIC_PATTERN = re.compile(
    rf"(?<!\d)(?<!\d[.,]){_OPERAND}(?:{_SEPARATOR}{_OPERAND})+(?!\d)(?![.,]\d)"
)

_SPLIT_PATTERN = re.compile(rf"({_SEPARATOR})")


def _is_year_like(operand: str) -> bool:
    return bool(re.fullmatch(r"\d{4}", operand)) and int(operand) in YEAR_RANGE


def _parse_expression(expression: str) -> tuple[str, str, str, str | None]:
    """
    Split an expression into (left, operator, right, result).

    Raises:
        ValueError: If the expression is not a two-operand operation, or if it
            is one of the shapes that only look like arithmetic.
    """
    parts = _SPLIT_PATTERN.split(expression.strip())
    operands = parts[0::2]
    separators = parts[1::2]
    operators = [separator.strip() for separator in separators]

    if not operators or operators[0] == EQUALS:
        raise ValueError(f"Not an arithmetic expression: {expression}")

    if len(operators) == 1:
        result = None
    elif len(operators) == 2 and operators[1] == EQUALS:
        result = operands[2]
    else:
        raise ValueError(f"Not a two-operand expression: {expression}")

    left, right = operands[0], operands[1]
    symbol = OPERATOR_ALIASES.get(operators[0], operators[0])

    tight = separators[0] == operators[0]
    if tight and symbol in {MINUS, DIVIDE} and (_is_year_like(left) or _is_year_like(right)):
        raise ValueError(f"Reads as a range, not an operation: {expression}")

    return left, operators[0], right, result


def format_arithmetic_bambara(expression: str) -> str:
    """
    Convert a written arithmetic expression to Bambara words.

    Args:
        expression: String such as "2 + 2", "8-5", "2 + 2 = 4"

    Returns:
        The spoken Bambara form of the expression

    Raises:
        ValueError: If the expression is not a two-operand operation

    Examples:
        >>> format_arithmetic_bambara("2 + 2")
        'fila fara fila kan'
        >>> format_arithmetic_bambara("10/2")
        'tan tila fila la'
        >>> format_arithmetic_bambara("2+2=4")
        'fila fara fila kan, o ye naani ye'
    """
    left, operator, right, result = _parse_expression(expression)
    return arithmetic_to_bambara(left, operator, right, result)


def _replace_arithmetic(match: re.Match) -> str | None:
    try:
        return format_arithmetic_bambara(match.group(0))
    except (ValueError, IndexError):
        return None


def find_arithmetic_spans(text: str) -> list[NumericSpan]:
    """
    Find arithmetic expressions in text and their Bambara expansions.

    Arithmetic spans lose against dates and times -- "24-12-2025" and "10:45"
    are read as what they are -- and win over measurements and bare numbers, so
    that the operands of an operation are never expanded on their own.
    """
    return find_spans(text, ARITHMETIC_PATTERN, ARITHMETIC, _replace_arithmetic)


def normalize_arithmetic_in_text(text: str) -> str:
    """
    Replace arithmetic expressions in text with their Bambara reading.

    Expressions that cannot be read as a single two-operand operation are left
    exactly as they were.

    Args:
        text: Input text with arithmetic expressions

    Returns:
        Text with arithmetic expressions converted to Bambara

    Examples:
        >>> normalize_arithmetic_in_text("A ko 2 + 2 = 4")
        'A ko fila fara fila kan, o ye naani ye'

        >>> normalize_arithmetic_in_text("A wolola 2020-2021 la")
        'A wolola 2020-2021 la'
    """
    return substitute(text, find_arithmetic_spans(text))

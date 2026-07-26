"""
Bambara number normalization module.

Converts between numerals and Bambara number words.
Supports integers up to millions and decimals.

Examples:
    >>> number_to_bambara(123)
    'kɛmɛ ni mugan ni saba'

    >>> bambara_to_number("kɛmɛ ni mugan ni saba")
    123

    >>> number_to_bambara(5.3)
    'duuru tomi saba'
"""

from __future__ import annotations

import re

from .spans import NUMBER, NumericSpan, find_spans, substitute

UNITS = [
    "fu",
    "kelen",
    "fila",
    "saba",
    "naani",
    "duuru",
    "wɔɔrɔ",
    "wolonwula",
    "seegin",
    "kɔnɔntɔn",
]

TENS = [
    "",
    "tan",
    "mugan",
    "bi saba",
    "bi naani",
    "bi duuru",
    "bi wɔɔrɔ",
    "bi wolonwula",
    "bi seegin",
    "bi kɔnɔntɔn",
]


TENS_ALT = {
    70: "bi wolonfila",
}


HUNDRED = "kɛmɛ"
THOUSAND = "waa"
MILLION = "miliyɔn"


DECIMAL_SEP = "tomi"

CONNECTOR = "ni"


def number_to_bambara(n: int | float | str) -> str:
    """
    Convert a number to Bambara words.

    Args:
        n: Number to convert (int, float, or string)

    Returns:
        Bambara representation of the number

    Examples:
        >>> number_to_bambara(0)
        'fu'
        >>> number_to_bambara(5)
        'duuru'
        >>> number_to_bambara(15)
        'tan ni duuru'
        >>> number_to_bambara(100)
        'kɛmɛ'
        >>> number_to_bambara(123)
        'kɛmɛ ni mugan ni saba'
        >>> number_to_bambara(1000)
        'waa kelen'
        >>> number_to_bambara(5.3)
        'duuru tomi saba'
    """
    if isinstance(n, str):
        n = n.strip()
        if n.count(".") > 1 or (n.count(",") > 0 and n.count(".") == 0):
            n = n.replace(".", "").replace(",", "")
        elif "," in n:
            n = n.replace(",", ".")

        if "." in n:
            n = float(n)
        else:
            n = int(n)

    if isinstance(n, float):
        return _float_to_bambara(n)

    return _int_to_bambara(int(n))


def _int_to_bambara(n: int) -> str:
    if n < 0:
        return f"kɔsɔn {_int_to_bambara(abs(n))}"

    if n == 0:
        return UNITS[0]

    if n < 10:
        return UNITS[n]

    if n < 20:
        remainder = n % 10
        if remainder == 0:
            return TENS[1]
        return f"{TENS[1]} {CONNECTOR} {UNITS[remainder]}"

    if n < 100:
        tens_idx = n // 10
        remainder = n % 10
        tens_word = TENS[tens_idx]
        if remainder == 0:
            return tens_word
        return f"{tens_word} {CONNECTOR} {UNITS[remainder]}"

    if n < 1000:
        hundreds = n // 100
        remainder = n % 100
        if hundreds == 1:
            prefix = HUNDRED
        else:
            prefix = f"{HUNDRED} {UNITS[hundreds]}"

        if remainder == 0:
            return prefix
        return f"{prefix} {CONNECTOR} {_int_to_bambara(remainder)}"

    if n < 1_000_000:
        thousands = n // 1000
        remainder = n % 1000
        prefix = f"{THOUSAND} {_int_to_bambara(thousands)}"

        if remainder == 0:
            return prefix
        return f"{prefix} {CONNECTOR} {_int_to_bambara(remainder)}"

    if n < 1_000_000_000:
        millions = n // 1_000_000
        remainder = n % 1_000_000
        prefix = f"{MILLION} {_int_to_bambara(millions)}"

        if remainder == 0:
            return prefix
        return f"{prefix} {CONNECTOR} {_int_to_bambara(remainder)}"

    return _digits_to_bambara(str(n))


def _float_to_bambara(n: float) -> str:
    str_n = str(n)
    if "." not in str_n:
        return _int_to_bambara(int(n))

    int_part, dec_part = str_n.split(".")
    int_word = _int_to_bambara(int(int_part)) if int_part else UNITS[0]

    dec_word = _digits_to_bambara(dec_part)

    return f"{int_word} {DECIMAL_SEP} {dec_word}"


def _digits_to_bambara(digits: str) -> str:
    return " ".join(UNITS[int(d)] for d in digits)


UNIT_VALUES = {word: i for i, word in enumerate(UNITS)}
UNIT_VALUES.update(
    {
        "kelenn": 1,
        "segin": 8,
        "kɔnɔtɔn": 9,
    }
)

TENS_VALUES = {
    "tan": 10,
    "mugan": 20,
    "bi saba": 30,
    "bi naani": 40,
    "bi duuru": 50,
    "bi wɔɔrɔ": 60,
    "bi wolonwula": 70,
    "bi wolonfila": 70,
    "bi seegin": 80,
    "bi segin": 80,
    "bi kɔnɔntɔn": 90,
    "bi kɔnɔtɔn": 90,
}

MULTIPLIER_VALUES = {
    "kɛmɛ": 100,
    "keme": 100,
    "waa": 1000,
    "wa": 1000,
    "milyɔn": 1_000_000,
    "milyon": 1_000_000,
}

NUMBER_TOKENS = (
    set(UNITS)
    | set(UNIT_VALUES.keys())
    | {"tan", "mugan", "bi"}
    | set(MULTIPLIER_VALUES.keys())
    | {CONNECTOR, DECIMAL_SEP, "tomi"}
)


def bambara_to_number(phrase: str) -> int | float:
    """
    Convert Bambara number words to a number.

    Args:
        phrase: Bambara number phrase

    Returns:
        Integer or float value

    Examples:
        >>> bambara_to_number("duuru")
        5
        >>> bambara_to_number("kɛmɛ ni mugan ni saba")
        123
        >>> bambara_to_number("duuru tomi saba")
        5.3

    Raises:
        ValueError: If phrase cannot be parsed
    """
    phrase = phrase.lower().strip()

    if DECIMAL_SEP in phrase or "tomi" in phrase:
        sep = DECIMAL_SEP if DECIMAL_SEP in phrase else "tomi"
        parts = phrase.split(sep)
        if len(parts) == 2:
            int_part = parts[0].strip()
            dec_part = parts[1].strip()

            int_val = _parse_bambara_int(int_part) if int_part else 0
            dec_val = _parse_decimal_digits(dec_part) if dec_part else "0"

            return float(f"{int_val}.{dec_val}")

    return _parse_bambara_int(phrase)


def _parse_bambara_int(phrase: str) -> int:
    phrase = phrase.strip()
    if not phrase:
        return 0

    if phrase in UNIT_VALUES:
        return UNIT_VALUES[phrase]

    for tens_phrase, value in TENS_VALUES.items():
        if phrase == tens_phrase:
            return value

        if phrase.startswith(tens_phrase + " "):
            remainder = phrase[len(tens_phrase) :].strip()
            if remainder.startswith(CONNECTOR):
                remainder = remainder[len(CONNECTOR) :].strip()
                return value + _parse_bambara_int(remainder)

    # parts = [p.strip() for p in phrase.split(CONNECTOR) if p.strip()]
    parts = [p.strip() for p in phrase.split(f" {CONNECTOR} ") if p.strip()]

    total = 0

    for part in parts:
        tokens = part.split()

        if not tokens:
            continue

        if tokens[0] == "bi" and len(tokens) > 1:
            rest = " ".join(tokens[1:])
            if rest in UNIT_VALUES:
                total += UNIT_VALUES[rest] * 10
                continue

        if tokens[0] in MULTIPLIER_VALUES:
            multiplier = MULTIPLIER_VALUES[tokens[0]]
            if len(tokens) > 1:
                sub_value = _parse_bambara_int(" ".join(tokens[1:]))
                total += multiplier * max(sub_value, 1)
            else:
                total += multiplier

        elif tokens[0] == "waa":
            if len(tokens) > 1:
                sub_value = _parse_bambara_int(" ".join(tokens[1:]))
                total += 1000 * max(sub_value, 1)
            else:
                total += 1000

        elif tokens[0] == "milyɔn" or tokens[0] == "milyon":
            if len(tokens) > 1:
                sub_value = _parse_bambara_int(" ".join(tokens[1:]))
                total += 1_000_000 * max(sub_value, 1)
            else:
                total += 1_000_000

        else:
            part_joined = " ".join(tokens)

            if part_joined in TENS_VALUES:
                total += TENS_VALUES[part_joined]
            elif part_joined in UNIT_VALUES:
                total += UNIT_VALUES[part_joined]
            elif tokens[0] in UNIT_VALUES:
                total += UNIT_VALUES[tokens[0]]
            else:
                raise ValueError(f"Cannot parse: '{part_joined}'")

    return total


def _parse_decimal_digits(phrase: str) -> str:
    parts = [p.strip() for p in phrase.split(CONNECTOR) if p.strip()]
    digits = []

    for part in parts:
        for token in part.split():
            if token in UNIT_VALUES:
                digits.append(str(UNIT_VALUES[token]))

    return "".join(digits) if digits else "0"


NUMBER_PATTERN = re.compile(r"\d[\d.,]*")


def _replace_number(match: re.Match) -> str | None:
    try:
        return number_to_bambara(match.group(0))
    except (ValueError, IndexError):
        return None


def find_number_spans(text: str) -> list[NumericSpan]:
    """
    Find bare numerals in text and their Bambara expansions.

    Numbers are the most generic numeric shape, so these spans lose against any
    overlapping date, time, or measurement span. See `spans.resolve_spans`.
    """
    return find_spans(text, NUMBER_PATTERN, NUMBER, _replace_number)


def normalize_numbers_in_text(text: str) -> str:
    """
    Replace all numerals in text with Bambara words.

    This expands every numeral it finds, including the digits of dates, times,
    and measurements. To expand mixed text, use
    `numeric.normalize_numeric_expressions`, which classifies each numeric span
    before expanding it.

    Args:
        text: Input text with numerals

    Returns:
        Text with numbers converted to Bambara words

    Examples:
        >>> normalize_numbers_in_text("A ye 5 wari di")
        'A ye duuru wari di'
        >>> normalize_numbers_in_text("Mɔgɔ 100 nana")
        'Mɔgɔ kɛmɛ nana'
    """
    return substitute(text, find_number_spans(text))


def denormalize_numbers_in_text(text: str) -> str:
    """
    Replace Bambara number words with numerals.

    This is a best-effort function that tries to identify number phrases.

    Args:
        text: Input text with Bambara number words

    Returns:
        Text with number words converted to numerals

    Examples:
        >>> denormalize_numbers_in_text("A ye duuru di")
        'A ye 5 di'
    """
    tokens = text.split()
    result = []
    buffer = []

    for token in tokens:
        token_lower = token.lower()

        is_number_token = (
            token_lower in NUMBER_TOKENS
            or token_lower in UNIT_VALUES
            or token_lower in MULTIPLIER_VALUES
            or token_lower.startswith("bi")
        )

        if is_number_token:
            buffer.append(token)
        else:
            if buffer:
                phrase = " ".join(buffer)
                try:
                    num = bambara_to_number(phrase)

                    if isinstance(num, float) and num == int(num):
                        result.append(str(int(num)))
                    else:
                        result.append(str(num))
                except ValueError:
                    result.extend(buffer)
                buffer = []
            result.append(token)

    if buffer:
        phrase = " ".join(buffer)
        try:
            num = bambara_to_number(phrase)
            if isinstance(num, float) and num == int(num):
                result.append(str(int(num)))
            else:
                result.append(str(num))
        except ValueError:
            result.extend(buffer)

    return " ".join(result)


def is_number_word(word: str) -> bool:
    word_lower = word.lower()
    return (
        word_lower in NUMBER_TOKENS or word_lower in UNIT_VALUES or word_lower in MULTIPLIER_VALUES
    )


ORDINAL_SUFFIX = "nan"


def number_to_ordinal(n: int) -> str:
    """
    Convert a number to Bambara ordinal.

    Args:
        n: Number to convert

    Returns:
        Ordinal form (e.g., "filanan" for 2nd)

    Note:
        1st is special: "fɔlɔ" (first)
    """
    if n == 1:
        return "fɔlɔ"

    cardinal = number_to_bambara(n)
    return f"{cardinal}{ORDINAL_SUFFIX}"


# __all__ = [
#     "number_to_bambara",
#     "bambara_to_number",
#     "normalize_numbers_in_text",
#     "denormalize_numbers_in_text",
#     "is_number_word",
#     "number_to_ordinal",
#     "UNITS",
#     "TENS",
#     "NUMBER_TOKENS",
# ]

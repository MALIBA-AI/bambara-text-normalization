# Copyright 2025 sudoping01.

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

from .numbers import bambara_to_number, number_to_bambara
from .spans import MEASUREMENT, NumericSpan, find_spans, substitute

KILOGARAMU = "kilogaramu"
GARAMU = "garamu"
MILIGARAMU = "miligaramu"
TONI = "tɔni"

KILOMETRE = "kilomɛtɛrɛ"
METRE = "mɛtɛrɛ"
SANTIMETRE = "santimɛtɛrɛ"
MILIMETRE = "milimɛtɛrɛ"

LITIRI = "litiri"
MILILITIRI = "mililitiri"

EKITARI = "ɛkitari"
METRE_KARE = "mɛtɛrɛ kare"

KONO = "kɔnɔ"  # "in" or "per"

UNIT_TO_BAMBARA = {
    "kg": KILOGARAMU,
    "g": GARAMU,
    "mg": MILIGARAMU,
    "t": TONI,
    "ton": TONI,
    "tonne": TONI,
    "km": KILOMETRE,
    "m": METRE,
    "cm": SANTIMETRE,
    "mm": MILIMETRE,
    "l": LITIRI,
    "L": LITIRI,
    "ml": MILILITIRI,
    "mL": MILILITIRI,
    "ha": EKITARI,
    "m²": METRE_KARE,
    "m2": METRE_KARE,
}

BAMBARA_TO_UNIT = {v: k for k, v in UNIT_TO_BAMBARA.items()}
BAMBARA_TO_UNIT[KILOGARAMU] = "kg"
BAMBARA_TO_UNIT[GARAMU] = "g"
BAMBARA_TO_UNIT[MILIGARAMU] = "mg"
BAMBARA_TO_UNIT[TONI] = "t"
BAMBARA_TO_UNIT[KILOMETRE] = "km"
BAMBARA_TO_UNIT[METRE] = "m"
BAMBARA_TO_UNIT[SANTIMETRE] = "cm"
BAMBARA_TO_UNIT[MILIMETRE] = "mm"
BAMBARA_TO_UNIT[LITIRI] = "L"
BAMBARA_TO_UNIT[MILILITIRI] = "mL"
BAMBARA_TO_UNIT[EKITARI] = "ha"
BAMBARA_TO_UNIT[METRE_KARE] = "m²"

UNIT_WORDS_TO_BAMBARA = {
    "kilogram": KILOGARAMU,
    "kilograms": KILOGARAMU,
    "kilogramme": KILOGARAMU,
    "kilogrammes": KILOGARAMU,
    "gram": GARAMU,
    "grams": GARAMU,
    "gramme": GARAMU,
    "grammes": GARAMU,
    "milligram": MILIGARAMU,
    "milligrams": MILIGARAMU,
    "ton": TONI,
    "tons": TONI,
    "tonne": TONI,
    "tonnes": TONI,
    "kilometer": KILOMETRE,
    "kilometers": KILOMETRE,
    "kilometre": KILOMETRE,
    "kilometres": KILOMETRE,
    "meter": METRE,
    "meters": METRE,
    "metre": METRE,
    "metres": METRE,
    "centimeter": SANTIMETRE,
    "centimeters": SANTIMETRE,
    "centimetre": SANTIMETRE,
    "centimetres": SANTIMETRE,
    "millimeter": MILIMETRE,
    "millimeters": MILIMETRE,
    "millimetre": MILIMETRE,
    "millimetres": MILIMETRE,
    "liter": LITIRI,
    "liters": LITIRI,
    "litre": LITIRI,
    "litres": LITIRI,
    "milliliter": MILILITIRI,
    "milliliters": MILILITIRI,
    "millilitre": MILILITIRI,
    "millilitres": MILILITIRI,
    "hectare": EKITARI,
    "hectares": EKITARI,
}


def measurement_to_bambara(value: float | int, unit: str) -> str:
    """
    Convert a measurement to Bambara.

    Args:
        value: Numeric value
        unit: Unit abbreviation or full word (e.g., "kg", "kilogram", "m", "meter")

    Returns:
        Bambara measurement string

    Examples:
        >>> measurement_to_bambara(5, "kg")
        'kilogaramu duuru'

        >>> measurement_to_bambara(100, "m")
        'mɛtɛrɛ kɛmɛ'

        >>> measurement_to_bambara(2.5, "L")
        'litiri fila tomi duuru'
    """
    unit_lower = unit.lower()

    if unit in UNIT_TO_BAMBARA:
        bambara_unit = UNIT_TO_BAMBARA[unit]
    elif unit_lower in UNIT_TO_BAMBARA:
        bambara_unit = UNIT_TO_BAMBARA[unit_lower]

    elif unit_lower in UNIT_WORDS_TO_BAMBARA:
        bambara_unit = UNIT_WORDS_TO_BAMBARA[unit_lower]
    else:
        raise ValueError(f"Unknown unit: {unit}")

    value_word = number_to_bambara(value)

    return f"{bambara_unit} {value_word}"


def bambara_to_measurement(phrase: str) -> tuple[float | int, str]:
    """
    Convert a Bambara measurement phrase to value and unit.

    Args:
        phrase: Bambara measurement phrase

    Returns:
        Tuple of (value, unit_abbreviation)

    Examples:
        >>> bambara_to_measurement("kilogaramu duuru")
        (5, 'kg')

        >>> bambara_to_measurement("mɛtɛrɛ kɛmɛ")
        (100, 'm')

        >>> bambara_to_measurement("litiri fila tomi duuru")
        (2.5, 'L')
    """
    phrase_lower = phrase.lower().strip()

    found_unit = None
    found_bambara = None
    value_phrase = None

    if METRE_KARE.lower() in phrase_lower:
        found_bambara = METRE_KARE
        found_unit = BAMBARA_TO_UNIT[METRE_KARE]
        value_phrase = phrase_lower.replace(METRE_KARE.lower(), "").strip()
    else:
        for bambara_unit, abbrev in BAMBARA_TO_UNIT.items():
            if bambara_unit.lower() in phrase_lower:
                if found_bambara is None or len(bambara_unit) > len(found_bambara):
                    found_bambara = bambara_unit
                    found_unit = abbrev

    if found_bambara is None:
        raise ValueError(f"No unit found in phrase: {phrase}")

    if value_phrase is None:
        value_phrase = phrase_lower.replace(found_bambara.lower(), "").strip()

    value = bambara_to_number(value_phrase)

    return (value, found_unit)


def format_measurement_bambara(measurement_str: str) -> str:
    """
    Format a measurement string to Bambara.

    Args:
        measurement_str: String like "5kg", "100 m", "2.5 L"

    Returns:
        Bambara measurement string

    Examples:
        >>> format_measurement_bambara("5kg")
        'kilogaramu duuru'

        >>> format_measurement_bambara("100 m")
        'mɛtɛrɛ kɛmɛ'

        >>> format_measurement_bambara("2.5 L")
        'litiri fila tomi duuru'
    """
    value, unit = parse_measurement_string(measurement_str)
    return measurement_to_bambara(value, unit)


def parse_measurement_string(s: str) -> tuple[float | int, str]:
    """
    Parse a measurement string like "5kg", "100 m", "2.5L".

    Returns:
        Tuple of (value, unit)
    """
    s = s.strip()

    pattern = r"^([\d]+(?:[.,]\d+)?)\s*([a-zA-Z²]+)$"
    match = re.match(pattern, s)

    if match:
        value_str = match.group(1).replace(",", ".")
        value = float(value_str)
        if value == int(value):
            value = int(value)
        unit = match.group(2)
        return (value, unit)

    raise ValueError(f"Cannot parse measurement: {s}")


def _build_measurement_pattern() -> re.Pattern:
    abbrev_units = "|".join(re.escape(u) for u in UNIT_TO_BAMBARA.keys())
    word_units = "|".join(re.escape(u) for u in UNIT_WORDS_TO_BAMBARA.keys())
    all_units = f"{abbrev_units}|{word_units}"
    return re.compile(rf"\b([\d]+(?:[.,]\d+)?)\s*({all_units})\b", re.IGNORECASE)


MEASUREMENT_PATTERN = _build_measurement_pattern()


def _replace_measurement(match: re.Match) -> str | None:
    try:
        value_str = match.group(1).replace(",", ".")
        value = float(value_str)
        if value == int(value):
            value = int(value)
        return measurement_to_bambara(value, match.group(2))
    except (ValueError, KeyError):
        return None


def find_measurement_spans(text: str) -> list[NumericSpan]:
    """
    Find measurement patterns in text and their Bambara expansions.

    Measurement spans lose against dates and times (a unit abbreviation can
    otherwise swallow part of a clock time or duration) and win over bare
    numbers.
    """
    return find_spans(text, MEASUREMENT_PATTERN, MEASUREMENT, _replace_measurement)


def normalize_measurements_in_text(text: str) -> str:
    """
    Replace measurement patterns in text with Bambara.

    Recognizes formats:
    - 5kg, 5 kg, 5 kilograms
    - 100m, 100 m, 100 meters
    - 2.5L, 2.5 L, 2.5 liters

    Args:
        text: Input text with measurements

    Returns:
        Text with measurements converted to Bambara

    Examples:
        >>> normalize_measurements_in_text("A ye 5 kg san")
        'A ye kilogaramu duuru san'

        >>> normalize_measurements_in_text("So in bɛ 100 m")
        'So in bɛ mɛtɛrɛ kɛmɛ'
    """
    return substitute(text, find_measurement_spans(text))


def denormalize_measurements_in_text(text: str) -> str:
    """
    Replace Bambara measurement expressions with standard formats.

    Args:
        text: Input text with Bambara measurements

    Returns:
        Text with measurements converted to standard format

    Examples:
        >>> denormalize_measurements_in_text("A ye kilogaramu duuru san")
        'A ye 5 kg san'

        >>> denormalize_measurements_in_text("So in bɛ mɛtɛrɛ kɛmɛ")
        'So in bɛ 100 m'
    """
    result = text

    metre_kare_pattern = rf"{METRE_KARE}\s+(\S+(?:\s+\S+)*?)(?=\s|$|[.,!?])"

    def replace_metre_kare(match: re.Match) -> str:
        try:
            value_phrase = match.group(1).strip()
            value = bambara_to_number(value_phrase)
            if value == int(value):
                value = int(value)
            return f"{value} m²"
        except (ValueError, KeyError):
            return match.group(0)

    result = re.sub(metre_kare_pattern, replace_metre_kare, result, flags=re.IGNORECASE)

    for bambara_unit, abbrev in BAMBARA_TO_UNIT.items():
        if bambara_unit == METRE_KARE:
            continue

        pattern = rf"{re.escape(bambara_unit)}\s+(\S+(?:\s+(?:ni\s+)?\S+)*?)(?=\s|$|[.,!?])"

        def make_replacer(unit_abbrev):
            def replace_unit(match: re.Match) -> str:
                try:
                    value_phrase = match.group(1).strip()
                    value_phrase = re.sub(r"[.,!?]+$", "", value_phrase)
                    value = bambara_to_number(value_phrase)
                    if value == int(value):
                        value = int(value)
                    return f"{value} {unit_abbrev}"
                except (ValueError, KeyError):
                    return match.group(0)

            return replace_unit

        result = re.sub(pattern, make_replacer(abbrev), result, flags=re.IGNORECASE)

    return result


def is_measurement_word(word: str) -> bool:
    word_lower = word.lower()

    bambara_units = {
        KILOGARAMU.lower(),
        GARAMU.lower(),
        MILIGARAMU.lower(),
        TONI.lower(),
        KILOMETRE.lower(),
        METRE.lower(),
        SANTIMETRE.lower(),
        MILIMETRE.lower(),
        LITIRI.lower(),
        MILILITIRI.lower(),
        EKITARI.lower(),
    }

    if word_lower in bambara_units:
        return True

    if word_lower in {"mɛtɛrɛ", "kare"}:
        return True

    return False


def get_unit_category(unit: str) -> str | None:
    """
    Get the category of a unit.

    Args:
        unit: Unit abbreviation or Bambara word

    Returns:
        Category string: "weight", "length", "volume", "area", or None

    Examples:
        >>> get_unit_category("kg")
        'weight'

        >>> get_unit_category("mɛtɛrɛ")
        'length'
    """
    weight_units = {KILOGARAMU, GARAMU, MILIGARAMU, TONI, "kg", "g", "mg", "t", "ton", "tonne"}
    length_units = {KILOMETRE, METRE, SANTIMETRE, MILIMETRE, "km", "m", "cm", "mm"}
    volume_units = {LITIRI, MILILITIRI, "l", "L", "ml", "mL"}
    area_units = {EKITARI, METRE_KARE, "ha", "m²", "m2"}

    unit_check = unit.lower() if unit not in {"L", "mL"} else unit

    if unit_check in weight_units or unit in weight_units:
        return "weight"
    elif unit_check in length_units or unit in length_units:
        return "length"
    elif unit_check in volume_units or unit in volume_units:
        return "volume"
    elif unit_check in area_units or unit in area_units:
        return "area"

    return None

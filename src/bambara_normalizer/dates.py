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
from datetime import date, datetime

from .numbers import bambara_to_number, number_to_bambara
from .spans import DATE, NumericSpan, find_spans, substitute

DAYS_OF_WEEK = {
    0: "Tɛnɛn",
    1: "Tarata",
    2: "Araba",
    3: "Alamisa",
    4: "Juma",
    5: "Sibiri",
    6: "Kari",
}

DAYS_OF_WEEK_REVERSE = {v.lower(): k for k, v in DAYS_OF_WEEK.items()}

DAYS_OF_WEEK_REVERSE.update(
    {
        "tεnεn": 0,
        "tenεn": 0,
        "tenen": 0,
        "tɛnɛn": 0,
        "tarata": 1,
        "araba": 2,
        "alamisa": 3,
        "juma": 4,
        "sibiri": 5,
        "kari": 6,
    }
)

MONTHS = {
    1: "Zanwuye",
    2: "Feburuye",
    3: "Marsi",
    4: "Awirili",
    5: "Mɛ",
    6: "Zuwen",
    7: "Zuluye",
    8: "Uti",
    9: "Sɛtanburu",
    10: "Oktɔburu",
    11: "Nɔwanburu",
    12: "Desanburu",
}

MONTHS_REVERSE = {v.lower(): k for k, v in MONTHS.items()}

MONTHS_REVERSE.update(
    {
        "zanwuye": 1,
        "feburuye": 2,
        "marsi": 3,
        "awirili": 4,
        "mɛ": 5,
        "mε": 5,
        "me": 5,
        "zuwen": 6,
        "zuluye": 7,
        "uti": 8,
        "sɛtanburu": 9,
        "sεtanburu": 9,
        "setanburu": 9,
        "sɛtamburu": 9,
        "oktɔburu": 10,
        "oktoburu": 10,
        "nɔwanburu": 11,
        "nowanburu": 11,
        "desanburu": 12,
    }
)

KALO = "kalo"
TILE = "tile"
SAN = "san"
DON = "don"


def _year_to_bambara(year: int) -> str:
    bambara = number_to_bambara(year)
    bambara = bambara.replace("waa", "baa")
    return bambara


def _bambara_to_year(phrase: str) -> int:
    normalized = phrase.strip()
    normalized = re.sub(r"\bbaa?\b", "waa", normalized)
    return int(bambara_to_number(normalized))


def date_to_bambara(
    year: int,
    month: int,
    day: int,
    include_kalo: bool = False,
    include_day_of_week: bool = False,
    day_of_week: int | None = None,
) -> str:
    """
    Convert a date to Bambara.

    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        day: Day of month (1-31)
        include_kalo: Include "kalo" (month) after month name
        include_day_of_week: Include day of week name
        day_of_week: Day of week (0=Monday, 6=Sunday), auto-calculated if None

    Returns:
        Bambara date string

    Examples:
        >>> date_to_bambara(2024, 10, 13)
        'Oktɔburu tile tan ni saba san waa fila ni mugan ni naani'

        >>> date_to_bambara(2008, 1, 25, include_kalo=True)
        'Zanwuye kalo tile mugan ni duuru san waa fila ni seegin'
    """
    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}")
    if day < 1 or day > 31:
        raise ValueError(f"Invalid day: {day}")

    parts = []

    if include_day_of_week:
        if day_of_week is None:
            day_of_week = date(year, month, day).weekday()
        parts.append(DAYS_OF_WEEK[day_of_week])

    month_name = MONTHS[month]
    if include_kalo:
        parts.append(f"{month_name} {KALO}")
    else:
        parts.append(month_name)

    day_word = number_to_bambara(day)
    parts.append(f"{TILE} {day_word}")

    # year_word = number_to_bambara(year)
    year_word = _year_to_bambara(year)
    parts.append(f"{SAN} {year_word}")

    return " ".join(parts)


def format_date_bambara(
    d: date | datetime | str, include_kalo: bool = False, include_day_of_week: bool = False
) -> str:
    """
    Format a date object or string to Bambara.

    Args:
        d: date, datetime, or string in format "YYYY-MM-DD" or "DD-MM-YYYY"
        include_kalo: Include "kalo" (month) after month name
        include_day_of_week: Include day of week name

    Returns:
        Bambara date string

    Examples:
        >>> from datetime import date
        >>> format_date_bambara(date(2024, 10, 13))
        'Oktɔburu tile tan ni saba san waa fila ni mugan ni naani'

        >>> format_date_bambara("13-10-2024")
        'Oktɔburu tile tan ni saba san waa fila ni mugan ni naani'
    """
    if isinstance(d, str):
        d = parse_date_string(d)

    if isinstance(d, datetime):
        d = d.date()

    return date_to_bambara(
        d.year,
        d.month,
        d.day,
        include_kalo=include_kalo,
        include_day_of_week=include_day_of_week,
        day_of_week=d.weekday(),
    )


def parse_date_string(s: str) -> date:
    s = s.strip()

    match = re.match(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return date(year, month, day)

    match = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return date(year, month, day)
    raise ValueError(f"Cannot parse date: {s}")


def bambara_to_date(phrase: str) -> date:
    """
    Convert a Bambara date phrase to a date object.

    Args:
        phrase: Bambara date phrase

    Returns:
        date object

    Examples:
        >>> bambara_to_date("Oktɔburu tile tan ni saba san waa fila ni mugan ni naani")
        datetime.date(2024, 10, 13)
    """
    phrase_lower = phrase.lower().strip()

    month = None
    month_end = 0
    for month_name, month_num in sorted(MONTHS_REVERSE.items(), key=lambda x: -len(x[0])):
        if phrase_lower.startswith(month_name):
            month = month_num
            month_end = len(month_name)
            break

    if month is None:
        raise ValueError(f"Cannot find month in: {phrase}")

    remainder = phrase_lower[month_end:].strip()

    if remainder.startswith(KALO):
        remainder = remainder[len(KALO) :].strip()

    if TILE not in remainder:
        raise ValueError(f"Cannot find 'tile' (day marker) in: {phrase}")

    tile_idx = remainder.index(TILE)
    remainder = remainder[tile_idx + len(TILE) :].strip()

    if SAN not in remainder:
        raise ValueError(f"Cannot find 'san' (year marker) in: {phrase}")

    san_idx = remainder.index(SAN)
    day_phrase = remainder[:san_idx].strip()
    year_phrase = remainder[san_idx + len(SAN) :].strip()

    day = bambara_to_number(day_phrase)
    # year = bambara_to_number(year_phrase)
    year = _bambara_to_year(year_phrase)

    return date(int(year), month, int(day))


def day_of_week_to_bambara(day: int) -> str:
    """
    Convert day of week number to Bambara.

    Args:
        day: 0=Monday, 6=Sunday (Python convention)

    Returns:
        Bambara day name
    """
    if day < 0 or day > 6:
        raise ValueError(f"Invalid day of week: {day}")
    return DAYS_OF_WEEK[day]


def bambara_to_day_of_week(name: str) -> int:
    """
    Convert Bambara day name to number.

    Args:
        name: Bambara day name

    Returns:
        Day number (0=Monday, 6=Sunday)
    """
    name_lower = name.lower().strip()
    if name_lower not in DAYS_OF_WEEK_REVERSE:
        raise ValueError(f"Unknown day name: {name}")
    return DAYS_OF_WEEK_REVERSE[name_lower]


def month_to_bambara(month: int) -> str:
    """
    Convert month number to Bambara.

    Args:
        month: 1-12

    Returns:
        Bambara month name
    """
    if month < 1 or month > 12:
        raise ValueError(f"Invalid month: {month}")
    return MONTHS[month]


def bambara_to_month(name: str) -> int:
    """
    Convert Bambara month name to number.

    Args:
        name: Bambara month name

    Returns:
        Month number (1-12)
    """
    name_lower = name.lower().strip()
    if name_lower not in MONTHS_REVERSE:
        raise ValueError(f"Unknown month name: {name}")
    return MONTHS_REVERSE[name_lower]


DATE_FRENCH_PATTERN = re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b")
DATE_ISO_PATTERN = re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b")


def find_date_spans(text: str, include_kalo: bool = False) -> list[NumericSpan]:
    """
    Find date patterns in text and their Bambara expansions.

    Recognizes DD-MM-YYYY / DD/MM/YYYY (French, tier 0) and YYYY-MM-DD (ISO,
    tier 1). Dates are the most specific numeric shape, so these spans win over
    any overlapping time, measurement, or number span.
    """

    def replace_date_french(match: re.Match) -> str | None:
        try:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            return date_to_bambara(year, month, day, include_kalo=include_kalo)
        except (ValueError, IndexError):
            return None

    def replace_date_iso(match: re.Match) -> str | None:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return date_to_bambara(year, month, day, include_kalo=include_kalo)
        except (ValueError, IndexError):
            return None

    return [
        *find_spans(text, DATE_FRENCH_PATTERN, DATE, replace_date_french),
        *find_spans(text, DATE_ISO_PATTERN, DATE, replace_date_iso, tier=1),
    ]


def normalize_dates_in_text(text: str, include_kalo: bool = False) -> str:
    """
    Replace date patterns in text with Bambara.

    Recognizes formats:
    - DD-MM-YYYY, DD/MM/YYYY (French format)
    - YYYY-MM-DD (ISO format)

    Args:
        text: Input text with dates
        include_kalo: Include "kalo" after month name

    Returns:
        Text with dates converted to Bambara

    Examples:
        >>> normalize_dates_in_text("A bɛ 13-10-2024 la")
        'A bɛ Oktɔburu tile tan ni saba san waa fila ni mugan ni naani la'
    """
    return substitute(text, find_date_spans(text, include_kalo=include_kalo))


def denormalize_dates_in_text(text: str) -> str:
    """
    Replace Bambara date expressions with DD-MM-YYYY format.

    Args:
        text: Input text with Bambara dates

    Returns:
        Text with dates converted to DD-MM-YYYY format
    """
    month_pattern = "|".join(sorted(MONTHS_REVERSE.keys(), key=lambda x: -len(x)))
    pattern = rf"({month_pattern})\s*(?:{KALO}\s+)?{TILE}\s+(.+?)\s+{SAN}\s+(.+?)(?=\s|$|[.,!?])"

    def replace_bambara_date(match: re.Match) -> str:
        try:
            month_name = match.group(1).lower()
            day_phrase = match.group(2).strip()
            year_phrase = match.group(3).strip()

            month = MONTHS_REVERSE[month_name]
            day = int(bambara_to_number(day_phrase))
            year = int(bambara_to_number(year_phrase))

            return f"{day:02d}-{month:02d}-{year}"
        except (ValueError, KeyError):
            return match.group(0)

    return re.sub(pattern, replace_bambara_date, text, flags=re.IGNORECASE)


def is_bambara_month(word: str) -> bool:
    return word.lower() in MONTHS_REVERSE


def is_bambara_day(word: str) -> bool:
    return word.lower() in DAYS_OF_WEEK_REVERSE

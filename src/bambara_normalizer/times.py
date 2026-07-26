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
from datetime import time, timedelta

from .numbers import bambara_to_number, number_to_bambara
from .spans import TIME, NumericSpan, find_spans, substitute

NEGE_KANYE = "Nɛgɛ kaɲɛ"
SANGA = "sanga"
NI = "ni"

LERE = "lɛrɛ"
MINITI = "miniti"
SEGONI = "segɔni"


def time_to_bambara(hour: int, minute: int = 0, second: int = 0) -> str:
    """
    Convert clock time to Bambara.

    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59), optional

    Returns:
        Bambara time string

    Examples:
        >>> time_to_bambara(1, 0)
        'Nɛgɛ kaɲɛ kelen'

        >>> time_to_bambara(1, 5)
        'Nɛgɛ kaɲɛ kelen ni sanga duuru'

        >>> time_to_bambara(7, 30)
        'Nɛgɛ kaɲɛ wolonwula ni sanga bi saba'

        >>> time_to_bambara(13, 50)
        'Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru'
    """
    if hour < 0 or hour > 23:
        raise ValueError(f"Invalid hour: {hour}")
    if minute < 0 or minute > 59:
        raise ValueError(f"Invalid minute: {minute}")
    if second < 0 or second > 59:
        raise ValueError(f"Invalid second: {second}")

    hour_word = number_to_bambara(hour)

    parts = [NEGE_KANYE, hour_word]

    if minute > 0 or second > 0:
        minute_word = number_to_bambara(minute)
        parts.append(f"{NI} {SANGA} {minute_word}")

        if second > 0:
            second_word = number_to_bambara(second)
            parts.append(f"{NI} {SEGONI} {second_word}")

    return " ".join(parts)


def format_time_bambara(t: time | str) -> str:
    """
    Format a time object or string to Bambara.

    Args:
        t: time object or string in format "HH:MM" or "HH:MM:SS"

    Returns:
        Bambara time string

    Examples:
        >>> from datetime import time
        >>> format_time_bambara(time(7, 30))
        'Nɛgɛ kaɲɛ wolonwula ni sanga bi saba'

        >>> format_time_bambara("13:50")
        'Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru'
    """
    if isinstance(t, str):
        t = parse_time_string(t)

    return time_to_bambara(t.hour, t.minute, t.second)


def parse_time_string(s: str) -> time:
    s = s.strip()

    match = re.match(r"(\d{1,2}):(\d{2}):(\d{2})", s)
    if match:
        hour, minute, second = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return time(hour, minute, second)

    match = re.match(r"(\d{1,2}):(\d{2})", s)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        return time(hour, minute)

    raise ValueError(f"Cannot parse time: {s}")


def bambara_to_time(phrase: str) -> time:
    """
    Convert a Bambara time phrase to a time object.

    Args:
        phrase: Bambara time phrase

    Returns:
        time object

    Examples:
        >>> bambara_to_time("Nɛgɛ kaɲɛ kelen")
        datetime.time(1, 0)

        >>> bambara_to_time("Nɛgɛ kaɲɛ wolonwula ni sanga bi saba")
        datetime.time(7, 30)
    """
    phrase_lower = phrase.lower().strip()

    nege_kanye_lower = NEGE_KANYE.lower()
    if not phrase_lower.startswith(nege_kanye_lower):
        raise ValueError(f"Time phrase must start with '{NEGE_KANYE}': {phrase}")

    remainder = phrase_lower[len(nege_kanye_lower) :].strip()

    sanga_lower = SANGA.lower()
    segoni_lower = SEGONI.lower()

    if sanga_lower in remainder:
        ni_sanga = f"{NI.lower()} {sanga_lower}"
        parts = remainder.split(ni_sanga)
        hour_phrase = parts[0].strip()
        minute_part = parts[1].strip() if len(parts) > 1 else ""

        hour = int(bambara_to_number(hour_phrase))

        second = 0
        if segoni_lower in minute_part:
            ni_segoni = f"{NI.lower()} {segoni_lower}"
            minute_parts = minute_part.split(ni_segoni)
            minute_phrase = minute_parts[0].strip()
            second_phrase = minute_parts[1].strip() if len(minute_parts) > 1 else ""
            if second_phrase:
                second = int(bambara_to_number(second_phrase))
        else:
            minute_phrase = minute_part

        minute = int(bambara_to_number(minute_phrase)) if minute_phrase else 0

        return time(hour, minute, second)
    else:
        hour = int(bambara_to_number(remainder))
        return time(hour, 0)


def duration_to_bambara(hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    """
    Convert a duration to Bambara.

    Args:
        hours: Number of hours
        minutes: Number of minutes
        seconds: Number of seconds

    Returns:
        Bambara duration string

    Examples:
        >>> duration_to_bambara(minutes=30)
        'miniti bi saba'

        >>> duration_to_bambara(hours=1, minutes=30)
        'lɛrɛ kelen ni miniti bi saba'

        >>> duration_to_bambara(hours=1, minutes=30, seconds=10)
        'lɛrɛ kelen ni miniti bi saba ni segɔni tan'
    """
    parts = []

    if hours > 0:
        hour_word = number_to_bambara(hours)
        parts.append(f"{LERE} {hour_word}")

    if minutes > 0:
        minute_word = number_to_bambara(minutes)
        parts.append(f"{MINITI} {minute_word}")

    if seconds > 0:
        second_word = number_to_bambara(seconds)
        parts.append(f"{SEGONI} {second_word}")

    if not parts:
        return f"{SEGONI} fu"

    return f" {NI} ".join(parts)


def format_duration_bambara(d: timedelta | str) -> str:
    """
    Format a timedelta or duration string to Bambara.

    Args:
        d: timedelta object or string like "1h30m", "30min", "1h30min10s"

    Returns:
        Bambara duration string

    Examples:
        >>> format_duration_bambara("30min")
        'miniti bi saba'

        >>> format_duration_bambara("1h30min")
        'lɛrɛ kelen ni miniti bi saba'

        >>> format_duration_bambara("1h30min10s")
        'lɛrɛ kelen ni miniti bi saba ni segɔni tan'
    """
    if isinstance(d, str):
        hours, minutes, seconds = parse_duration_string(d)
    elif isinstance(d, timedelta):
        total_seconds = int(d.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
    else:
        raise TypeError(f"Expected timedelta or str, got {type(d)}")

    return duration_to_bambara(hours, minutes, seconds)


def parse_duration_string(s: str) -> tuple[int, int, int]:
    """
    Parse a duration string like "1h30m", "30min", "1h30min10s".

    Returns:
        Tuple of (hours, minutes, seconds)
    """
    s = s.strip().lower()
    hours = 0
    minutes = 0
    seconds = 0

    hour_match = re.search(r"(\d+)\s*h", s)
    if hour_match:
        hours = int(hour_match.group(1))

    min_match = re.search(r"(\d+)\s*(?:min|m)(?!i)", s)
    if min_match:
        minutes = int(min_match.group(1))
    else:
        min_match = re.search(r"(\d+)\s*min", s)
        if min_match:
            minutes = int(min_match.group(1))

    sec_match = re.search(r"(\d+)\s*s(?:ec)?", s)
    if sec_match:
        seconds = int(sec_match.group(1))

    return hours, minutes, seconds


def bambara_to_duration(phrase: str) -> tuple[int, int, int]:
    """
    Convert a Bambara duration phrase to hours, minutes, seconds.

    Args:
        phrase: Bambara duration phrase

    Returns:
        Tuple of (hours, minutes, seconds)

    Examples:
        >>> bambara_to_duration("miniti bi saba")
        (0, 30, 0)

        >>> bambara_to_duration("lɛrɛ kelen ni miniti bi saba")
        (1, 30, 0)
    """
    phrase_lower = phrase.lower().strip()

    hours = 0
    minutes = 0
    seconds = 0

    lere_lower = LERE.lower()
    miniti_lower = MINITI.lower()
    segoni_lower = SEGONI.lower()

    parts = [p.strip() for p in phrase_lower.split(f" {NI.lower()} ")]

    for part in parts:
        if lere_lower in part:
            hour_phrase = part.replace(lere_lower, "").strip()
            hours = int(bambara_to_number(hour_phrase))
        elif miniti_lower in part:
            minute_phrase = part.replace(miniti_lower, "").strip()
            minutes = int(bambara_to_number(minute_phrase))
        elif segoni_lower in part:
            second_phrase = part.replace(segoni_lower, "").strip()
            seconds = int(bambara_to_number(second_phrase))

    return hours, minutes, seconds


CLOCK_PATTERN = re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b")
DURATION_PATTERN = re.compile(
    r"\b\d+\s*h(?:\s*\d+\s*(?:min|m))?(?:\s*\d+\s*s(?:ec)?)?\b|\b\d+\s*min(?:\s*\d+\s*s(?:ec)?)?\b|\b\d+\s*s(?:ec)?\b",
    re.IGNORECASE,
)


def _replace_clock_time(match: re.Match) -> str | None:
    try:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3)) if match.group(3) else 0
        return time_to_bambara(hour, minute, second)
    except (ValueError, IndexError):
        return None


def _replace_duration(match: re.Match) -> str | None:
    try:
        hours, minutes, seconds = parse_duration_string(match.group(0))
        if hours > 0 or minutes > 0 or seconds > 0:
            return duration_to_bambara(hours, minutes, seconds)
        return None
    except (ValueError, IndexError):
        return None


def find_time_spans(text: str) -> list[NumericSpan]:
    """
    Find time patterns in text and their Bambara expansions.

    Recognizes HH:MM / HH:MM:SS clock times (tier 0) and XhYmZs durations
    (tier 1). Time spans lose against dates and win over measurements and bare
    numbers.
    """
    return [
        *find_spans(text, CLOCK_PATTERN, TIME, _replace_clock_time),
        *find_spans(text, DURATION_PATTERN, TIME, _replace_duration, tier=1),
    ]


def normalize_times_in_text(text: str) -> str:
    """
    Replace time patterns in text with Bambara.

    Recognizes formats:
    - HH:MM, HH:MM:SS (clock time)
    - XhYm, XhYmin, XhYmZs (duration)

    Args:
        text: Input text with times

    Returns:
        Text with times converted to Bambara

    Examples:
        >>> normalize_times_in_text("A nana 7:30 la")
        'A nana Nɛgɛ kaɲɛ wolonwula ni sanga bi saba la'

        >>> normalize_times_in_text("A tagara 1h30min")
        'A tagara lɛrɛ kelen ni miniti bi saba'
    """
    return substitute(text, find_time_spans(text))


def denormalize_times_in_text(text: str) -> str:
    """
    Replace Bambara time expressions with standard formats.

    Args:
        text: Input text with Bambara times

    Returns:
        Text with times converted to standard format
    """
    nege_pattern = rf"{NEGE_KANYE}\s+(.+?)(?:\s+{NI}\s+{SANGA}\s+(.+?))?(?=\s|$|[.,!?])"

    def replace_clock(match: re.Match) -> str:
        try:
            hour_phrase = match.group(1).strip()
            hour = int(bambara_to_number(hour_phrase))

            if match.group(2):
                minute_phrase = match.group(2).strip()
                minute = int(bambara_to_number(minute_phrase))
            else:
                minute = 0

            return f"{hour:02d}:{minute:02d}"
        except (ValueError, KeyError):
            return match.group(0)

    text = re.sub(nege_pattern, replace_clock, text, flags=re.IGNORECASE)

    duration_pattern = rf"(?:{LERE}\s+(.+?))?(?:\s*{NI}\s*)?(?:{MINITI}\s+(.+?))?(?:\s*{NI}\s*)?(?:{SEGONI}\s+(.+?))?(?=\s|$|[.,!?])"

    def replace_duration(match: re.Match) -> str:
        try:
            result_parts = []

            if match.group(1):
                hours = int(bambara_to_number(match.group(1).strip()))
                result_parts.append(f"{hours}h")

            if match.group(2):
                minutes = int(bambara_to_number(match.group(2).strip()))
                result_parts.append(f"{minutes}min")

            if match.group(3):
                seconds = int(bambara_to_number(match.group(3).strip()))
                result_parts.append(f"{seconds}s")

            if result_parts:
                return "".join(result_parts)
            return match.group(0)
        except (ValueError, KeyError):
            return match.group(0)

    if LERE.lower() in text.lower() or MINITI.lower() in text.lower():
        text = re.sub(duration_pattern, replace_duration, text, flags=re.IGNORECASE)

    return text


def is_time_word(word: str) -> bool:
    time_words = {
        NEGE_KANYE.lower(),
        "nɛgɛ",
        "kaɲɛ",
        SANGA.lower(),
        LERE.lower(),
        MINITI.lower(),
        SEGONI.lower(),
    }
    return word.lower() in time_words

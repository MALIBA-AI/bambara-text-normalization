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
import unicodedata

from .config import BambaraNormalizerConfig
from .numeric import normalize_numeric_expressions


class BambaraNormalizer:
    """Bambara text normalizer for ASR evaluation.

    Handles Bambara-specific linguistic features including:
    - Special characters: ɛ, ɔ, ɲ, ŋ
    - Grammatical contractions: b', t', y', n', k' (with disambiguation)
    - Tone diacritics: à, á, è, é, etc.
    - Legacy orthography: è==>ɛ, ny==>ɲ, ng==>ŋ

    Contraction modes:
    - "expand": b'a → bɛ a (default, with disambiguation for k')
    - "contract": bɛ a → b'a (reverse, simpler - no disambiguation needed)
    - "preserve": don't touch contractions

    Example:
        >>> normalizer = BambaraNormalizer()
        >>> normalizer("B'a fɔ́!")
        'bɛ a fɔ'

        >>> config = BambaraNormalizerConfig(contraction_mode="contract")
        >>> normalizer = BambaraNormalizer(config)
        >>> normalizer("bɛ a fɔ")
        "b'a fɔ"
    """

    SPECIAL_CHARS = {
        "ɛ": "\u025b",
        "Ɛ": "\u0190",
        "ɔ": "\u0254",
        "Ɔ": "\u0186",
        "ɲ": "\u0272",
        "Ɲ": "\u019d",
        "ŋ": "\u014b",
        "Ŋ": "\u014a",
    }

    APOSTROPHE_VARIANTS = [
        "\u0027",
        "\u2019",
        "\u02bc",
        "\u2018",
        "\u0060",
        "\u00b4",
        "\u2032",
        "\uff07",
        "\u02b9",
        "\u02bb",
    ]

    KE_POSTPOSITIONS = {
        "la",
        "ye",
        "fɛ",
        "kɔnɔ",
        "kɔ",
        "kɔrɔ",
        "da",
        "daa",
        "kun",
        "ɲɛ",
        "ɲɛɛ",
        "ɲɛfɛ",
        "bolo",
        "sɛmɛ",
        "cɛ",
        "cɛma",
        "kɔfɛ",
        "kosɔn",
        "kama",
    }

    REPORTED_SPEECH_MARKERS = {
        "ko",
        "ka",
        "kana",
        "tɛ",
        "te",
        "bɛ",
        "be",
        "bɛna",
        "bena",
        "tɛna",
        "tena",
        "tun",
        "mana",
    }

    CLAUSE_MARKERS = {
        "ka",
        "kana",
        "tɛ",
        "te",
        "bɛ",
        "be",
        "bɛna",
        "bena",
        "tɛna",
        "tena",
        "tun",
        "mana",
        "yɛrɛ",
        "de",
        "dɛ",
    }

    SIMPLE_CONTRACTIONS = {
        "b'": "bɛ ",
        "t'": "tɛ ",
        "y'": "ye ",
        "m'": "ma ",
        "s'": "sa ",
    }

    EXTENDED_CONTRACTIONS = {
        "b'a": "bɛ a",
        "t'a": "tɛ a",
        "y'a": "ye a",
        "b'i": "bɛ i",
        "t'i": "tɛ i",
        "y'i": "ye i",
        "b'o": "bɛ o",
        "t'o": "tɛ o",
        "y'o": "ye o",
        "y'u": "ye u",
        "b'u": "bɛ u",
        "t'u": "tɛ u",
    }

    CONTRACTION_EXPANSIONS = {
        "b'": "bɛ",
        "t'": "tɛ",
        "y'": "ye",
        "m'": "ma",
        "s'": "sa",
    }

    CONTRACTION_PATTERNS = {
        "bɛ": "b'",
        "tɛ": "t'",
        "ye": "y'",
        "ni": "n'",
        "na": "n'",
        "ka": "k'",
        "kɛ": "k'",
        "ko": "k'",
        "ma": "m'",
        "sa": "s'",
    }

    VOWEL_STARTERS = {"a", "i", "o", "u", "e", "ɛ", "ɔ", "an", "anw", "aw", "ale", "olu"}

    LEGACY_ORTHOGRAPHY = {
        "è": "ɛ",
        "È": "Ɛ",
        "ò": "ɔ",
        "Ò": "Ɔ",
        "ê": "ɛ",
        "Ê": "Ɛ",
        "ô": "ɔ",
        "Ô": "Ɔ",
        "ε": "ɛ",
        "э": "ɛ",
    }

    LEGACY_DIGRAPHS = {
        "ny": "ɲ",
        "Ny": "Ɲ",
        "NY": "Ɲ",
        "ng": "ŋ",
        "Ng": "Ŋ",
        "NG": "Ŋ",
    }

    SENEGALESE_VARIANTS = {"ñ": "ɲ", "Ñ": "Ɲ"}

    TONE_DIACRITICS = {"\u0300", "\u0301", "\u030c", "\u0302", "\u0304"}

    PUNCTUATION_CATEGORIES = {"Po", "Ps", "Pe", "Pi", "Pf", "Pd", "Pc"}

    def __init__(self, config: BambaraNormalizerConfig | None = None):
        self.config = config or BambaraNormalizerConfig()
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        apostrophe_chars = "".join(re.escape(c) for c in self.APOSTROPHE_VARIANTS)
        self._apostrophe_pattern = re.compile(f"[{apostrophe_chars}]")
        self._whitespace_pattern = re.compile(r"\s+")
        self._repetition_pattern = re.compile(r"(.)\1{2,}")
        self._number_pattern = re.compile(r"\d+")
        self._build_punctuation_pattern()

    def _build_punctuation_pattern(self) -> None:
        punct_chars = []
        for i in range(0x10000):
            char = chr(i)
            if unicodedata.category(char) in self.PUNCTUATION_CATEGORIES:
                if char not in self.APOSTROPHE_VARIANTS:
                    punct_chars.append(char)
        self._punctuation_pattern = re.compile(f"[{''.join(re.escape(c) for c in punct_chars)}]")

    def __call__(self, text: str) -> str:
        return self.normalize(text)

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        text = unicodedata.normalize("NFC", text)

        if self.config.normalize_apostrophes:
            text = self._normalize_apostrophes(text)

        mode = self.config.contraction_mode
        if mode == "expand":
            text = self._expand_contractions(text)

        elif mode == "contract":
            text = self._contract_text(text)

        if self.config.normalize_legacy_orthography:
            text = self._normalize_legacy_orthography(text)

        # One classification pass over every numeric span, so the result does not
        # depend on the order dates/times/measurements/numbers are expanded in.
        text = normalize_numeric_expressions(
            text,
            dates=self.config.expand_dates,
            times=self.config.expand_times,
            measurements=self.config.expand_measurements,
            numbers=self.config.expand_numbers,
        )

        if self.config.normalize_special_chars:
            text = self._normalize_special_chars(text)

        if self.config.lowercase:
            text = self._lowercase(text)

        if not self.config.preserve_tones:
            text = self._remove_tone_marks(text)

        elif self.config.remove_diacritics_except_tones:
            text = self._remove_non_tone_diacritics(text)

        if self.config.remove_punctuation:
            text = self._remove_punctuation(text)

        if self.config.strip_repetitions:
            text = self._strip_repetitions(text)

        if self.config.normalize_compounds:
            text = self._normalize_compounds(text)

        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)

        return text

    def _contract_text(self, text: str) -> str:
        """
        Contract expanded forms to contracted forms.

        bɛ a → b'a
        tɛ a → t'a
        ye a → y'a
        ni a → n'a
        na a → n'a
        ka a → k'a
        kɛ a → k'a
        ko a → k'a

        This is simpler than expansion - no disambiguation needed!
        """
        words = text.split()
        result = []
        i = 0

        while i < len(words):
            word = words[i]
            word_lower = self._strip_tones_and_punct(word.lower())

            if word_lower in self.CONTRACTION_PATTERNS and i + 1 < len(words):
                next_word = words[i + 1]
                next_word_lower = self._strip_tones_and_punct(next_word.lower())

                if next_word_lower and next_word_lower[0] in "aeiouɛɔ":
                    contracted_prefix = self.CONTRACTION_PATTERNS[word_lower]
                    contracted = contracted_prefix + next_word
                    result.append(contracted)
                    i += 2  # Skip both words
                    continue

            result.append(word)
            i += 1

        return " ".join(result)

    def _normalize_apostrophes(self, text: str) -> str:
        return self._apostrophe_pattern.sub("'", text)

    def _expand_contractions(self, text: str) -> str:
        text = self._expand_k_contraction(text)

        text = self._expand_n_contraction(text)

        for contracted, expanded in self.EXTENDED_CONTRACTIONS.items():
            pattern = re.compile(re.escape(contracted), re.IGNORECASE)
            text = pattern.sub(expanded, text)

        for contracted, expanded in self.SIMPLE_CONTRACTIONS.items():
            pattern = re.compile(re.escape(contracted), re.IGNORECASE)
            text = pattern.sub(expanded, text)

        return text

    def _get_lookahead_base(self, word: str) -> str | None:
        word_lower = word.lower()

        if re.match(r"k'[aeiouɛɔ]", word_lower):
            return None  # Signal recursive prediction needed

        for prefix, expanded in self.CONTRACTION_EXPANSIONS.items():
            if word_lower.startswith(prefix):
                return expanded

        return self._strip_tones_and_punct(word_lower)

    def _predict_k_expansion(self, words: list[str], idx: int) -> str:
        if idx >= len(words):
            return "ka"

        word = words[idx]
        k_match = re.match(r"k'([aeiouɛɔ]\w*)", word, re.IGNORECASE)
        if not k_match:
            return "ka"

        if idx + 1 < len(words):
            next_word = words[idx + 1]
            next_base = self._get_lookahead_base(next_word)

            if next_base is None:
                predicted_next = self._predict_k_expansion(words, idx + 1)
                if predicted_next == "ka":
                    return "ko"
                else:
                    return "ka"

            if next_base in self.KE_POSTPOSITIONS:
                return "kɛ"

            if next_base in self.CLAUSE_MARKERS:
                return "ko"

            if next_base == "ma":
                if idx + 2 < len(words):
                    word_after_ma = words[idx + 2]
                    word_after_ma_base = self._strip_tones_and_punct(word_after_ma.lower())

                    if idx + 3 < len(words):
                        third_word = words[idx + 3]
                        third_word_base = self._strip_tones_and_punct(third_word.lower())
                        if third_word_base == "ye":
                            return "kɛ"

                    if word_after_ma_base in self.REPORTED_SPEECH_MARKERS:
                        return "ko"

                return "kɛ"

        return "ka"

    def _expand_k_contraction(self, text: str) -> str:
        words = text.split()
        result = []
        i = 0

        while i < len(words):
            word = words[i]
            k_match = re.match(r"k'([aeiouɛɔ]\w*)", word, re.IGNORECASE)

            if k_match:
                pronoun = k_match.group(1)

                if i + 1 < len(words):
                    next_word = words[i + 1]
                    next_word_base = self._get_lookahead_base(next_word)

                    if next_word_base is None:
                        predicted = self._predict_k_expansion(words, i + 1)
                        if predicted == "ka":
                            expanded = f"ko {pronoun}"
                        else:
                            expanded = f"ka {pronoun}"
                    elif next_word_base == "ma":
                        if i + 2 < len(words):
                            word_after_ma = words[i + 2]
                            word_after_ma_base = self._strip_tones_and_punct(word_after_ma.lower())

                            if i + 3 < len(words):
                                third_word = words[i + 3]
                                third_word_base = self._strip_tones_and_punct(third_word.lower())
                                if third_word_base == "ye":
                                    expanded = f"kɛ {pronoun}"
                                elif word_after_ma_base in self.REPORTED_SPEECH_MARKERS:
                                    expanded = f"ko {pronoun}"
                                else:
                                    expanded = f"kɛ {pronoun}"
                            elif word_after_ma_base in self.REPORTED_SPEECH_MARKERS:
                                expanded = f"ko {pronoun}"
                            else:
                                expanded = f"kɛ {pronoun}"
                        else:
                            expanded = f"kɛ {pronoun}"
                    elif next_word_base in self.KE_POSTPOSITIONS:
                        expanded = f"kɛ {pronoun}"
                    elif next_word_base in self.CLAUSE_MARKERS:
                        expanded = f"ko {pronoun}"
                    else:
                        expanded = f"ka {pronoun}"
                else:
                    expanded = f"ka {pronoun}"

                result.append(expanded)
            else:
                result.append(word)

            i += 1

        return " ".join(result)

    def _expand_n_contraction(self, text: str) -> str:
        words = text.split()
        result = []
        i = 0

        while i < len(words):
            word = words[i]
            n_match = re.match(r"n'([aeiouɛɔ]\w*)", word, re.IGNORECASE)

            if n_match:
                pronoun = n_match.group(1)

                if i + 1 < len(words):
                    next_word = words[i + 1]
                    next_word_base = self._strip_tones_and_punct(next_word.lower())

                    if next_word_base == "ma":
                        expanded = f"na {pronoun}"
                    else:
                        expanded = f"ni {pronoun}"
                else:
                    expanded = f"ni {pronoun}"

                result.append(expanded)
            else:
                result.append(word)

            i += 1

        return " ".join(result)

    def _strip_tones(self, word: str) -> str:
        nfd = unicodedata.normalize("NFD", word)
        return "".join(c for c in nfd if c not in self.TONE_DIACRITICS)

    def _strip_tones_and_punct(self, word: str) -> str:
        nfd = unicodedata.normalize("NFD", word)
        word = "".join(c for c in nfd if c not in self.TONE_DIACRITICS)
        word = unicodedata.normalize("NFC", word)
        return "".join(
            c for c in word if unicodedata.category(c) not in self.PUNCTUATION_CATEGORIES
        )

    def _normalize_legacy_orthography(self, text: str) -> str:
        for old, new in self.LEGACY_DIGRAPHS.items():
            text = text.replace(old, new)
        for old, new in self.LEGACY_ORTHOGRAPHY.items():
            text = text.replace(old, new)
        for old, new in self.SENEGALESE_VARIANTS.items():
            text = text.replace(old, new)
        return text

    def _normalize_special_chars(self, text: str) -> str:
        result = []
        for char in text:
            if char in "εЄє":
                result.append("ɛ")
            elif char in "ΕЭэ":
                result.append("Ɛ")
            else:
                result.append(char)
        return "".join(result)

    def _lowercase(self, text: str) -> str:
        return text.lower()

    def _remove_tone_marks(self, text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        result = [c for c in text if c not in self.TONE_DIACRITICS]
        return unicodedata.normalize("NFC", "".join(result))

    def _remove_non_tone_diacritics(self, text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        result = []
        for char in text:
            category = unicodedata.category(char)
            if category != "Mn" or char in self.TONE_DIACRITICS:
                result.append(char)
        return unicodedata.normalize("NFC", "".join(result))

    def _remove_punctuation(self, text: str) -> str:
        return self._punctuation_pattern.sub("", text)

    def _strip_repetitions(self, text: str) -> str:
        return self._repetition_pattern.sub(r"\1\1", text)

    def _normalize_compounds(self, text: str) -> str:
        compounds = [
            (r"\b(bi)\s+(saba|naani|duuru|wɔɔrɔ|wolonwula|segin|kɔnɔntɔn)\b", r"\1\2"),
            (r"\b(tan)\s+(ni)\s+", r"\1 \2 "),
        ]
        for pattern, replacement in compounds:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        return self._whitespace_pattern.sub(" ", text).strip()

    def normalize_for_comparison(self, text: str) -> str:
        original_config = self.config
        self.config = BambaraNormalizerConfig.for_wer_evaluation()
        result = self.normalize(text)
        self.config = original_config
        return result

    def normalize_batch(self, texts: list[str]) -> list[str]:
        return [self.normalize(text) for text in texts]

    def get_normalization_diff(self, text: str) -> dict[str, str]:
        result = {"original": text}
        text = unicodedata.normalize("NFC", text)
        result["nfc_normalized"] = text

        if self.config.normalize_apostrophes:
            text = self._normalize_apostrophes(text)
            result["apostrophes_normalized"] = text

        mode = self.config.contraction_mode
        if mode == "expand":
            text = self._expand_contractions(text)
            result["contractions_expanded"] = text
        elif mode == "contract":
            text = self._contract_text(text)
            result["contractions_contracted"] = text

        if self.config.normalize_legacy_orthography:
            text = self._normalize_legacy_orthography(text)
            result["legacy_normalized"] = text

        if self.config.lowercase:
            text = self._lowercase(text)
            result["lowercased"] = text

        if not self.config.preserve_tones:
            text = self._remove_tone_marks(text)
            result["tones_removed"] = text

        if self.config.remove_punctuation:
            text = self._remove_punctuation(text)
            result["punctuation_removed"] = text

        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)
            result["whitespace_normalized"] = text

        result["final"] = text
        return result


def create_normalizer(
    preset: str = "standard", mode: str = "expand", **kwargs
) -> BambaraNormalizer:
    """
    Factory function to create a normalizer with preset configuration.

    Args:
        preset: One of "standard", "wer", "cer", "preserving_tones", "minimal"
        mode: Contraction mode - "expand", "contract", or "preserve"
        **kwargs: Override specific configuration options

    Returns:
        Configured BambaraNormalizer instance.

    Example:
        >>> normalizer = create_normalizer("wer", mode="contract")
        >>> normalizer("bɛ a fɔ")
        "b'a fɔ"
    """
    presets = {
        "standard": BambaraNormalizerConfig,
        "wer": BambaraNormalizerConfig.for_wer_evaluation,
        "cer": BambaraNormalizerConfig.for_cer_evaluation,
        "preserving_tones": BambaraNormalizerConfig.preserving_tones,
        "minimal": BambaraNormalizerConfig.minimal,
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Choose from: {list(presets.keys())}")

    if preset in ("wer", "cer", "preserving_tones"):
        config = presets[preset](mode=mode)
    else:
        config = presets[preset]()
        config.contraction_mode = mode

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    return BambaraNormalizer(config)

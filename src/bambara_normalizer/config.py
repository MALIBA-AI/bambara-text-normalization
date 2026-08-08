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

from dataclasses import dataclass
from enum import Enum


class ContractionMode(Enum):
    EXPAND = "expand"
    CONTRACT = "contract"
    PRESERVE = "preserve"


class NormalizationLevel(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


@dataclass
class BambaraNormalizerConfig:
    """
    Configuration for Bambara text normalization.

    Attributes:
        contraction_mode: How to handle contractions ("expand", "contract", "preserve")
        preserve_tones: Keep tone diacritics (à, á, etc.)
        normalize_legacy_orthography: Convert old spellings (è→ɛ, ny→ɲ)
        lowercase: Convert to lowercase
        remove_punctuation: Remove punctuation marks
        normalize_whitespace: Collapse multiple spaces
        normalize_apostrophes: Standardize apostrophe variants
        normalize_special_chars: Handle variant forms of ɛ, ɔ, ɲ, ŋ
        expand_numbers: Convert digits to Bambara words
        expand_arithmetic: Convert arithmetic expressions (2 + 2 = 4) to Bambara
        expand_dates: Convert date patterns (DD-MM-YYYY) to Bambara
        remove_diacritics_except_tones: Remove non-tonal diacritics
        handle_french_loanwords: Apply French word normalization
        strip_repetitions: Normalize repeated characters
        normalize_compounds: Standardize compound word spacing
        expand_times: Convert time patterns to Bambara
    """

    contraction_mode: str = "expand"
    preserve_tones: bool = True
    normalize_legacy_orthography: bool = True
    lowercase: bool = True
    remove_punctuation: bool = True
    normalize_whitespace: bool = True
    normalize_apostrophes: bool = True
    normalize_special_chars: bool = True
    expand_numbers: bool = False
    expand_arithmetic: bool = False
    expand_dates: bool = False
    expand_times: bool = False
    expand_measurements: bool = False
    remove_diacritics_except_tones: bool = False
    handle_french_loanwords: bool = True
    strip_repetitions: bool = False
    normalize_compounds: bool = False

    @property
    def expand_contractions(self) -> bool:
        """Backward compatibility: True if mode is 'expand'."""
        return self.contraction_mode == "expand"

    @expand_contractions.setter
    def expand_contractions(self, value: bool) -> None:
        """Backward compatibility setter."""
        if value:
            self.contraction_mode = "expand"
        else:
            self.contraction_mode = "preserve"

    @classmethod
    def for_wer_evaluation(cls, mode: str = "expand") -> BambaraNormalizerConfig:
        return cls(
            contraction_mode=mode,
            preserve_tones=False,
            normalize_legacy_orthography=True,
            lowercase=True,
            remove_punctuation=True,
            normalize_whitespace=True,
            normalize_apostrophes=True,
            normalize_special_chars=True,
            expand_numbers=True,
            expand_arithmetic=True,
            expand_measurements=True,
            expand_dates=True,
            expand_times=True,
            remove_diacritics_except_tones=True,
            handle_french_loanwords=True,
            strip_repetitions=True,
            normalize_compounds=True,
        )

    @classmethod
    def for_cer_evaluation(cls, mode: str = "expand") -> BambaraNormalizerConfig:
        return cls(
            contraction_mode=mode,
            preserve_tones=False,
            normalize_legacy_orthography=True,
            lowercase=True,
            remove_punctuation=True,
            normalize_whitespace=True,
            normalize_apostrophes=True,
            normalize_special_chars=True,
            expand_numbers=True,
            expand_arithmetic=True,
            expand_dates=True,
            expand_times=True,
            remove_diacritics_except_tones=True,
            handle_french_loanwords=True,
            strip_repetitions=False,
            normalize_compounds=True,
        )

    @classmethod
    def preserving_tones(cls, mode: str = "expand") -> BambaraNormalizerConfig:
        return cls(
            contraction_mode=mode,
            preserve_tones=True,
            normalize_legacy_orthography=True,
            lowercase=True,
            remove_punctuation=True,
            normalize_whitespace=True,
            normalize_apostrophes=True,
            normalize_special_chars=True,
            expand_numbers=False,
            expand_arithmetic=False,
            expand_dates=False,
            expand_times=False,
            remove_diacritics_except_tones=False,
            handle_french_loanwords=False,
            strip_repetitions=False,
            normalize_compounds=False,
        )

    @classmethod
    def minimal(cls) -> BambaraNormalizerConfig:
        return cls(
            contraction_mode="preserve",
            preserve_tones=True,
            normalize_legacy_orthography=False,
            lowercase=True,
            remove_punctuation=False,
            normalize_whitespace=True,
            normalize_apostrophes=True,
            normalize_special_chars=False,
            expand_numbers=False,
            expand_arithmetic=False,
            expand_dates=False,
            expand_times=False,
            remove_diacritics_except_tones=False,
            handle_french_loanwords=False,
            strip_repetitions=False,
            normalize_compounds=False,
        )


@dataclass
class EvaluationResult:
    wer: float
    cer: float
    mer: float = 0.0
    wil: float = 0.0
    wip: float = 0.0
    der: float | None = None

    word_substitutions: int = 0
    word_deletions: int = 0
    word_insertions: int = 0
    word_hits: int = 0
    total_reference_words: int = 0

    char_substitutions: int = 0
    char_deletions: int = 0
    char_insertions: int = 0
    char_hits: int = 0
    total_reference_chars: int = 0

    reference_normalized: str = ""
    hypothesis_normalized: str = ""

    def __str__(self) -> str:
        return (
            f"WER: {self.wer:.2%} "
            f"(S={self.word_substitutions}, D={self.word_deletions}, I={self.word_insertions}, H={self.word_hits}, N={self.total_reference_words})\n"
            f"CER: {self.cer:.2%} "
            f"(S={self.char_substitutions}, D={self.char_deletions}, I={self.char_insertions}, H={self.char_hits}, N={self.total_reference_chars})\n"
            f"MER: {self.mer:.2%} | WIL: {self.wil:.2%} | WIP: {self.wip:.2%}"
            + (f"\nDER: {self.der:.2%}" if self.der is not None else "")
        )

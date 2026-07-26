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
Command-line interface for Bambara text normalizer.

Usage:
    bambara-normalize "B'a fɔ́"
    bambara-normalize --mode expand "B'a fɔ́"
    bambara-normalize --mode contract "bɛ a fɔ"
    bambara-normalize --preset wer --mode contract "text"
    echo "text" | bambara-normalize
    bambara-normalize --file input.txt --output output.txt
    bambara-normalize --evaluate ref.txt hyp.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evaluation import BambaraEvaluator
from .normalizer import BambaraNormalizer, BambaraNormalizerConfig, create_normalizer


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bambara-normalize",
        description="Bambara text normalizer for ASR evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Normalize text (expand contractions, default):
    bambara-normalize "B'a fɔ́"
    bambara-normalize --mode expand "k'a ta"

  Contract expanded forms:
    bambara-normalize --mode contract "bɛ a fɔ"
    bambara-normalize --mode contract "ka a ta"

  Preserve contractions (don't touch):
    bambara-normalize --mode preserve "B'a fɔ"

  Use WER preset with contraction:
    bambara-normalize --preset wer --mode contract "ka a ta"

  Process file:
    bambara-normalize --file input.txt --output normalized.txt
    bambara-normalize --mode contract --file input.txt

  Evaluate ASR output:
    bambara-normalize --evaluate reference.txt hypothesis.txt
    bambara-normalize --evaluate --mode contract ref.txt hyp.txt

  Pipe from stdin:
    echo "B'a fɔ́" | bambara-normalize
    echo "bɛ a fɔ" | bambara-normalize --mode contract
""",
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="Text to normalize (reads from stdin if not provided)",
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["expand", "contract", "preserve"],
        default="expand",
        help="Contraction mode: expand (default), contract, or preserve",
    )

    parser.add_argument(
        "--preset",
        "-p",
        choices=["standard", "wer", "cer", "minimal", "preserving_tones"],
        default="standard",
        help="Normalization preset (default: standard)",
    )

    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        help="Input file to normalize",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file (default: stdout)",
    )

    parser.add_argument(
        "--evaluate",
        "-e",
        nargs=2,
        metavar=("REF", "HYP"),
        type=Path,
        help="Evaluate hypothesis against reference (provide two files)",
    )

    parser.add_argument(
        "--preserve-tones",
        action="store_true",
        help="Preserve tone marks during normalization",
    )

    parser.add_argument(
        "--expand-numbers",
        action="store_true",
        help="Expand numbers to Bambara words",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show normalization steps",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 2.0.0",
    )

    return parser.parse_args(args)


def normalize_text(
    text: str,
    preset: str,
    mode: str = "expand",
    preserve_tones: bool = False,
    expand_numbers: bool = False,
    debug: bool = False,
) -> str:
    kwargs = {}
    if preserve_tones:
        kwargs["preserve_tones"] = True
    if expand_numbers:
        kwargs["expand_numbers"] = True

    normalizer = create_normalizer(preset, mode=mode, **kwargs)

    if debug:
        diff = normalizer.get_normalization_diff(text)
        print("Normalization steps:", file=sys.stderr)
        for step, value in diff.items():
            print(f"  {step}: {value}", file=sys.stderr)
        print(file=sys.stderr)

    return normalizer(text)


def process_file(
    input_path: Path,
    output_path: Path | None,
    normalizer: BambaraNormalizer,
) -> None:
    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    normalized = [normalizer(line.rstrip("\n")) for line in lines]

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(normalized) + "\n")
        print(f"Normalized output written to {output_path}", file=sys.stderr)
    else:
        for line in normalized:
            print(line)


def run_evaluation(
    ref_path: Path,
    hyp_path: Path,
    preset: str,
    mode: str = "expand",
) -> None:
    with open(ref_path, encoding="utf-8") as f:
        references = [line.strip() for line in f if line.strip()]

    with open(hyp_path, encoding="utf-8") as f:
        hypotheses = [line.strip() for line in f if line.strip()]

    if len(references) != len(hypotheses):
        print(
            f"Error: Reference ({len(references)} lines) and hypothesis "
            f"({len(hypotheses)} lines) have different lengths",
            file=sys.stderr,
        )
        sys.exit(1)

    config = BambaraNormalizerConfig.for_wer_evaluation(mode=mode)
    evaluator = BambaraEvaluator(config=config)
    aggregate, individual = evaluator.evaluate_batch(references, hypotheses)

    print("=" * 60)
    print("Bambara ASR Evaluation Results")
    print("=" * 60)
    print(f"Reference file: {ref_path}")
    print(f"Hypothesis file: {hyp_path}")
    print(f"Normalization preset: {preset}")
    print(f"Contraction mode: {mode}")
    print(f"Total utterances: {len(references)}")
    print("-" * 60)
    print(f"Word Error Rate (WER): {aggregate.wer:.2%}")
    print(f"  Substitutions: {aggregate.word_substitutions}")
    print(f"  Deletions: {aggregate.word_deletions}")
    print(f"  Insertions: {aggregate.word_insertions}")
    print(f"  Reference words: {aggregate.total_reference_words}")
    print("-" * 60)
    print(f"Character Error Rate (CER): {aggregate.cer:.2%}")
    print(f"  Substitutions: {aggregate.char_substitutions}")
    print(f"  Deletions: {aggregate.char_deletions}")
    print(f"  Insertions: {aggregate.char_insertions}")
    print(f"  Reference chars: {aggregate.total_reference_chars}")
    print("=" * 60)


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)

    try:
        if parsed.evaluate:
            ref_path, hyp_path = parsed.evaluate
            run_evaluation(ref_path, hyp_path, parsed.preset, parsed.mode)
            return 0

        kwargs = {}
        if parsed.preserve_tones:
            kwargs["preserve_tones"] = True
        if parsed.expand_numbers:
            kwargs["expand_numbers"] = True

        normalizer = create_normalizer(parsed.preset, mode=parsed.mode, **kwargs)

        if parsed.file:
            process_file(parsed.file, parsed.output, normalizer)
            return 0

        if parsed.text:
            text = parsed.text
        elif not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Error: No input provided", file=sys.stderr)
            print(
                "Usage: bambara-normalize <text> or echo <text> | bambara-normalize",
                file=sys.stderr,
            )
            return 1

        result = normalize_text(
            text,
            parsed.preset,
            parsed.mode,
            parsed.preserve_tones,
            parsed.expand_numbers,
            parsed.debug,
        )

        if parsed.output:
            with open(parsed.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"Output written to {parsed.output}", file=sys.stderr)
        else:
            print(result)

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

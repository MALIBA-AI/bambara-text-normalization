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
    bambara-normalize --input input.txt --output output.txt
    bambara-normalize --evaluate ref.txt hyp.txt
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .evaluation import BambaraEvaluator
from .normalizer import BambaraNormalizer, create_normalizer

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


class Mode(str, Enum):
    """How contractions are handled."""

    EXPAND = "expand"
    CONTRACT = "contract"
    PRESERVE = "preserve"


class Preset(str, Enum):
    """Bundled normalization presets."""

    STANDARD = "standard"
    WER = "wer"
    CER = "cer"
    MINIMAL = "minimal"
    PRESERVING_TONES = "preserving_tones"


HELP_EPILOG = """
[bold]Examples[/bold]

  [dim]# Normalize text (expand contractions, default)[/dim]
  bambara-normalize "B'a fɔ́"

  [dim]# Contract expanded forms[/dim]
  bambara-normalize --mode contract "bɛ a fɔ"

  [dim]# WER preset[/dim]
  bambara-normalize --preset wer "K'a fɔ́!"

  [dim]# Process a corpus line by line[/dim]
  bambara-normalize --input corpus.txt --output normalized.txt

  [dim]# Evaluate ASR output[/dim]
  bambara-normalize --evaluate ref.txt hyp.txt
  bambara-normalize --evaluate --detailed ref.txt hyp.txt

  [dim]# Pipe from stdin[/dim]
  echo "B'a fɔ́" | bambara-normalize
"""


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"bambara-normalize [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


def _fail(message: str) -> typer.Exit:
    """Report an error on stderr and return the exception to raise."""
    err_console.print(f"[bold red]Error:[/bold red] {message}", soft_wrap=True)
    return typer.Exit(code=1)


def _echo(text: str) -> None:
    """Write a result to stdout verbatim, safe to pipe."""
    console.print(text, markup=False, highlight=False, soft_wrap=True)


def _show_diff(normalizer: BambaraNormalizer, text: str) -> None:
    """Render the intermediate normalization steps on stderr."""
    table = Table(title="Normalization steps", title_justify="left", header_style="bold")
    table.add_column("Step", style="cyan", no_wrap=True)
    table.add_column("Result")

    for step, value in normalizer.get_normalization_diff(text).items():
        table.add_row(step, Text(str(value)))

    err_console.print(table)


def normalize_text(
    text: str,
    preset: str,
    mode: str = "expand",
    preserve_tones: bool = False,
    expand_numbers: bool = False,
    debug: bool = False,
) -> str:
    """Normalize a single string with the given preset and overrides."""
    kwargs = {}
    if preserve_tones:
        kwargs["preserve_tones"] = True
    if expand_numbers:
        kwargs["expand_numbers"] = True

    normalizer = create_normalizer(preset, mode=mode, **kwargs)

    if debug:
        _show_diff(normalizer, text)

    return normalizer(text)


def process_file(
    input_path: Path,
    output_path: Optional[Path],
    normalizer: BambaraNormalizer,
) -> None:
    """Normalize a file line by line, to `output_path` or stdout."""
    with open(input_path, encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    if output_path is None:
        for line in lines:
            _echo(normalizer(line))
        return

    normalized = []
    with err_console.status(f"Normalizing {input_path}...", spinner="dots"):
        normalized = [normalizer(line) for line in lines]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(normalized) + "\n")

    err_console.print(
        f"[green]✓[/green] {len(normalized)} line(s) written to [bold]{output_path}[/bold]",
        soft_wrap=True,
    )


def _metrics_table(result, title: str) -> Table:
    """Word- and character-level metrics for one evaluation result."""
    table = Table(title=title, title_justify="left", header_style="bold", box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Rate", justify="right", style="bold")
    table.add_column("Sub", justify="right")
    table.add_column("Del", justify="right")
    table.add_column("Ins", justify="right")
    table.add_column("N", justify="right")

    table.add_row(
        "WER",
        f"{result.wer:.2%}",
        str(result.word_substitutions),
        str(result.word_deletions),
        str(result.word_insertions),
        str(result.total_reference_words),
    )
    table.add_row(
        "CER",
        f"{result.cer:.2%}",
        str(result.char_substitutions),
        str(result.char_deletions),
        str(result.char_insertions),
        str(result.total_reference_chars),
    )
    return table


def _detailed_table(individual) -> Table:
    """Per-utterance WER/CER."""
    table = Table(title="Per-utterance", title_justify="left", header_style="bold")
    table.add_column("#", justify="right", style="dim")
    table.add_column("WER", justify="right")
    table.add_column("CER", justify="right")
    table.add_column("Reference", overflow="fold")
    table.add_column("Hypothesis", overflow="fold")

    for index, result in enumerate(individual, start=1):
        style = "red" if result.wer > 0 else "green"
        table.add_row(
            str(index),
            f"[{style}]{result.wer:.2%}[/{style}]",
            f"{result.cer:.2%}",
            Text(result.reference_normalized),
            Text(result.hypothesis_normalized),
        )
    return table


def run_evaluation(
    ref_path: Path,
    hyp_path: Path,
    preset: str,
    mode: str = "expand",
    detailed: bool = False,
) -> None:
    """Compare a hypothesis file against a reference file, line by line."""
    with open(ref_path, encoding="utf-8") as f:
        references = [line.strip() for line in f if line.strip()]

    with open(hyp_path, encoding="utf-8") as f:
        hypotheses = [line.strip() for line in f if line.strip()]

    if len(references) != len(hypotheses):
        raise _fail(
            f"Reference ({len(references)} lines) and hypothesis "
            f"({len(hypotheses)} lines) have different lengths"
        )

    normalizer = create_normalizer(preset, mode=mode)
    evaluator = BambaraEvaluator(config=normalizer.config)

    with err_console.status("Evaluating...", spinner="dots"):
        aggregate, individual = evaluator.evaluate_batch(references, hypotheses)

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="dim")
    summary.add_column()
    summary.add_row("reference", str(ref_path))
    summary.add_row("hypothesis", str(hyp_path))
    summary.add_row("preset", preset)
    summary.add_row("mode", mode)
    summary.add_row("utterances", str(len(references)))

    console.print(
        Panel(summary, title="Bambara ASR Evaluation", title_align="left", border_style="cyan")
    )
    console.print(_metrics_table(aggregate, "Aggregate"))

    if detailed:
        console.print()
        console.print(_detailed_table(individual))


@app.command(epilog=HELP_EPILOG)
def normalize(
    text: Optional[List[str]] = typer.Argument(
        None,
        metavar="[TEXT]...",
        help="Text to normalize, or REF and HYP files with --evaluate. Reads stdin if omitted.",
        show_default=False,
    ),
    mode: Mode = typer.Option(
        Mode.EXPAND, "--mode", "-m", help="Contraction handling.", show_choices=True
    ),
    preset: Preset = typer.Option(
        Preset.STANDARD, "--preset", "-p", help="Normalization preset.", show_choices=True
    ),
    input_file: Optional[Path] = typer.Option(
        None,
        "--input",
        "-f",
        "--file",
        help="Input file to normalize, one utterance per line.",
        show_default=False,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Write results here instead of stdout.", show_default=False
    ),
    evaluate: bool = typer.Option(
        False, "--evaluate", "-e", help="Evaluate: the two arguments are REF and HYP files."
    ),
    detailed: bool = typer.Option(
        False, "--detailed", help="With --evaluate, also show per-utterance metrics."
    ),
    preserve_tones: bool = typer.Option(
        False, "--preserve-tones", help="Keep tone marks during normalization."
    ),
    expand_numbers: bool = typer.Option(
        False, "--expand-numbers", help="Expand digits to Bambara words."
    ),
    debug: bool = typer.Option(False, "--debug", help="Show intermediate normalization steps."),
    plain: bool = typer.Option(False, "--plain", help="Unstyled output, even on a terminal."),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """
    Bambara (Bamanankan) text normalizer for ASR evaluation.

    Normalizes contractions, orthography, tones and numeric expressions so that
    WER/CER measure recognition errors rather than spelling variation.
    """
    arguments = list(text or [])

    if evaluate:
        if len(arguments) != 2:
            raise _fail("--evaluate needs exactly two files: REF and HYP")
        run_evaluation(
            Path(arguments[0]), Path(arguments[1]), preset.value, mode.value, detailed=detailed
        )
        return

    overrides = {}
    if preserve_tones:
        overrides["preserve_tones"] = True
    if expand_numbers:
        overrides["expand_numbers"] = True

    normalizer = create_normalizer(preset.value, mode=mode.value, **overrides)

    if input_file is not None:
        if arguments:
            raise _fail("Pass either --input or text arguments, not both")
        process_file(input_file, output, normalizer)
        return

    if arguments:
        source = " ".join(arguments)
    elif not sys.stdin.isatty():
        source = sys.stdin.read().strip()
    else:
        err_console.print("[bold red]Error:[/bold red] No input provided")
        err_console.print(
            "Usage: [bold]bambara-normalize <text>[/bold] "
            "or [bold]echo <text> | bambara-normalize[/bold]"
        )
        raise typer.Exit(code=1)

    if debug:
        _show_diff(normalizer, source)

    result = normalizer(source)

    if output is not None:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        err_console.print(
            f"[green]✓[/green] Output written to [bold]{output}[/bold]", soft_wrap=True
        )
        return

    if console.is_terminal and not plain:
        console.print(
            Panel(
                Text(result),
                title=f"{preset.value} · {mode.value}",
                title_align="left",
                border_style="cyan",
                highlight=False,
            )
        )
    else:
        _echo(result)


def _build_command() -> click.Command:
    """The click command behind `app`, without click's empty env var hints."""
    command = typer.main.get_command(app)
    for param in command.params:
        if getattr(param, "envvar", None) is None:
            param.show_envvar = False
    return command


def main(args: Optional[List[str]] = None) -> int:
    """Entry point for the `bambara-normalize` console script."""
    try:
        code = _build_command().main(
            args=args, prog_name="bambara-normalize", standalone_mode=False
        )
    except click.UsageError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc.format_message()}", soft_wrap=True)
        err_console.print("Try [bold]bambara-normalize --help[/bold] for help.")
        return exc.exit_code
    except click.ClickException as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc.format_message()}", soft_wrap=True)
        return exc.exit_code
    except click.exceptions.Abort:
        err_console.print("[yellow]Aborted.[/yellow]")
        return 130
    except FileNotFoundError as exc:
        err_console.print(
            f"[bold red]Error:[/bold red] File not found: {exc.filename or exc}", soft_wrap=True
        )
        return 1
    except Exception as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}", soft_wrap=True)
        return 1

    return code if isinstance(code, int) else 0


if __name__ == "__main__":
    sys.exit(main())

<h1 align="center">
    Bambara Text Normalizer
</h1>
<p align="center">
    <em>Text Normalization & ASR Evaluation Framework for Bambara (Bamanankan)</em>
</p>
<p align="center">
    <a href="#installation">Installation</a> •
    <a href="#text-normalization">Normalization</a> •
    <a href="#asr-evaluation-framework">ASR Evaluation</a> •
    <a href="#contraction-modes">Modes</a> •
    <a href="#command-line-interface">CLI</a> •
    <a href="#linguistic-decisions">Linguistics</a> •
    <a href="#references">References</a>
</p>

<!-- prettier-ignore -->
<p align="center">
    <a href="https://pypi.org/project/djelia/"><img src="https://img.shields.io/pypi/v/bambara-text-normalizer.svg?label=pypi%20(stable)" alt="PyPI version"></a>
</p>

---

## Purpose

This tool serves **two complementary purposes** for Bambara language processing:

| Purpose | Description |
|---------|-------------|
| **Text Normalization** | Standardize Bambara text for any downstream NLP task (TTS, MT, NER, etc.) |
| **ASR Evaluation** | Fair WER/CER computation that accounts for valid orthographic variation |

> [!NOTE]
> Bambara orthography allows variation: the same utterance can be written as `k'a ta` or `ka a ta`  both are correct. Without normalization, evaluation metrics unfairly penalize models for human writing inconsistencies rather than actual recognition errors.

---
## Installation

```bash
# Core library only
pip install bambara-text-normalizer

# Install with CLI support
pip install "bambara-text-normalizer[cli]"

# Install everything
pip install "bambara-text-normalizer[all]"
```
```bash
pip install git+https://github.com/sudoping01/bambara-text-normalization.git
```
---

## Text Normalization



```python
from bambara_normalizer import normalize

# Default: expand contractions
normalize("⁠Ne k’a ma ko ayi")           
normalize("⁠K’ale t’a fɛ k’a kɛ")    
normalize("⁠K’i k’i janto i yɛrɛ la")        


# Contract mode: collapse expanded forms
normalize("Ne ko a ma ko ayi", mode="contract")    
normalize("Ko ale tɛ a fɛ ka o kɛ", mode="contract")    
normalize("Ko i ka i janto i yɛrɛ la", mode="contract")    

# Preserve mode: don't touch contractions
normalize("K’i k’i janto i yɛrɛ la", mode="preserve")     
```

### Custom Settings

```python
from bambara_normalizer import normalize

# Full control over normalization
text = normalize(
    "Ka na son k’o k’a la",
    mode="expand",                      # "expand" | "contract" | "preserve"
    preserve_tones=False,               
    normalize_legacy_orthography=True, 
    lowercase=True,                     
    remove_punctuation=False,           
    normalize_whitespace=True,         
    normalize_apostrophes=True,         
    normalize_special_chars=True,    
    expand_dates = False,
    expand_measurements=False, 
    expand_numbers=False,  
    expand_times=False,            
    remove_diacritics_except_tones=False,  
    handle_french_loanwords=True,   
    strip_repetitions=False,       
    normalize_compounds=True, 
)
```

### Using BambaraNormalizer Class

For repeated normalization with consistent settings:

```python
from bambara_normalizer import BambaraNormalizer, BambaraNormalizerConfig


config = BambaraNormalizerConfig(contraction_mode="expand") # change it to "contract" or preserve
normalizer = BambaraNormalizer(config)
normalizer("A y'a fɔ")      
normalizer("k'a la")   

# Contraction mode
config = BambaraNormalizerConfig(contraction_mode="contract")
normalizer = BambaraNormalizer(config)
normalizer("bɛ a fɔ")     
normalizer("ka a ta")     
```

### Predefined Configuration Presets

```python
from bambara_normalizer import BambaraNormalizer, BambaraNormalizerConfig

# For WER evaluation (aggressive normalization, removes tones)
normalizer = BambaraNormalizer(BambaraNormalizerConfig.for_wer_evaluation())

# For WER with contract mode
normalizer = BambaraNormalizer(BambaraNormalizerConfig.for_wer_evaluation(mode="contract"))

# For CER evaluation
normalizer = BambaraNormalizer(BambaraNormalizerConfig.for_cer_evaluation())

# Preserve tone marks
normalizer = BambaraNormalizer(BambaraNormalizerConfig.preserving_tones())

# Minimal normalization (only essential fixes)
normalizer = BambaraNormalizer(BambaraNormalizerConfig.minimal())
```


---

## Number Normalization

The normalizer supports bidirectional number conversion between digits and Bambara words (TN/ITN).

### With Normalizer
```python
from bambara_normalizer import normalize

normalize("A ye 100 sɔrɔ", expand_numbers=True)   # => "a ye kɛmɛ sɔrɔ"
normalize("A ye 100 sɔrɔ", expand_numbers=False)  # => "a ye 100 sɔrɔ"

# WER preset has expand_numbers=True by default
normalize("A ye 5 ta", preset="wer")  # => "a ye duuru ta"
```

### Digits to Words (Text Normalization)
```python
from bambara_normalizer import number_to_bambara, normalize_numbers_in_text


number_to_bambara(5)        # => "duuru"
number_to_bambara(123)      # => "kɛmɛ ni mugan ni saba"
number_to_bambara(1000)     # => "waa kelen"
number_to_bambara(5.3)      # => "duuru tomi saba"

# In text
normalize_numbers_in_text("A ye 5 wari di")      # => "A ye duuru wari di"
normalize_numbers_in_text("Mɔgɔ 100 nana")       # => "Mɔgɔ kɛmɛ nana"
normalize_numbers_in_text("N ye shekɛ 1000 sɔrɔ") # => "N ye shekɛ waa kelen sɔrɔ"
```

### Words to Digits (Inverse Text Normalization)
```python
from bambara_normalizer import bambara_to_number, denormalize_numbers_in_text

bambara_to_number("duuru")                    # => 5
bambara_to_number("kɛmɛ ni mugan ni saba")    # => 123
bambara_to_number("duuru tomi saba")          # => 5.3

# In text
denormalize_numbers_in_text("A ye duuru di a ma")  # => "A ye 5 di a ma"
denormalize_numbers_in_text("Mɔgɔ kɛmɛ nana")      # => "Mɔgɔ 100 nana"
```



### Number Vocabulary

| Value | Bambara | Value | Bambara |
|-------|---------|-------|---------|
| 0 | fu | 10 | tan |
| 1 | kelen | 20 | mugan |
| 2 | fila | 30 | bi saba |
| 3 | saba | 40 | bi naani |
| 4 | naani | 50 | bi duuru |
| 5 | duuru | 100 | kɛmɛ |
| 6 | wɔɔrɔ | 1000 | waa |
| 7 | wolonwula | 1,000,000 | miliyɔn |
| 8 | seegin | decimal | tomi |
| 9 | kɔnɔntɔn | connector | ni |

---
---

## Date Normalization

The normalizer supports bidirectional date conversion between standard formats and Bambara expressions (TN/ITN).

### With Normalizer
```python
from bambara_normalizer import normalize

normalize("A bɛ na 13-10-2024 la", expand_dates=True)   # ==> "a bɛ na oktɔburu tile tan ni saba san Baa fila ni mugan ni naani la"
normalize("A bɛ na 13-10-2024 la", expand_dates=False)  # => "a bɛ na 13-10-2024 la"

# WER preset has expand_dates=True by default
normalize("A bɛ na 25-01-2008 la", preset="wer")  # => "a bɛ na zanwuye tile mugan ni duuru san Baa fila ni seegin la"
```

### Date to Bambara (Text Normalization)
```python
from bambara_normalizer import date_to_bambara, format_date_bambara, normalize_dates_in_text
from datetime import date

# Single dates
date_to_bambara(2024, 10, 13)      # => "Oktɔburu tile tan ni saba san baa fila ni mugan ni naani"
date_to_bambara(2008, 1, 25)       # => "Zanwuye tile mugan ni duuru san baa fila ni seegin"

# With "kalo" (month) included
date_to_bambara(2024, 10, 13, include_kalo=True)  # => "Oktɔburu kalo tile tan ni saba san ..."

# With day of week
date_to_bambara(2024, 10, 13, include_day_of_week=True)  # => "Kari Oktɔburu tile ..." (Sunday)

# From date object or string
format_date_bambara(date(2024, 10, 13))  # => "Oktɔburu tile tan ni saba san ..."
format_date_bambara("13-10-2024")        # => "Oktɔburu tile tan ni saba san ..."

# In text
normalize_dates_in_text("A bɛ na 13-10-2024 la")  # => "A bɛ na Oktɔburu tile tan ni saba san baa fila ni mugan ni naani la"
```

### Bambara to Date (Inverse Text Normalization)
```python
from bambara_normalizer import bambara_to_date

bambara_to_date("Oktɔburu tile tan ni saba san baa fila ni mugan ni naani")
# => datetime.date(2024, 10, 13)

bambara_to_date("Zanwuye tile mugan ni duuru san baa fila ni seegin")
# => datetime.date(2008, 1, 25)
```

### Date Format

Bambara dates follow this structure:
```
[Month] (kalo) tile [day] san [year]
```

Example: **13-10-2024** => `Oktɔburu tile tan ni saba san baa fila ni mugan ni naani`

Literal translation: "October day thirteen year two thousand twenty-four"

### Days of the Week

| Day | Bambara | Day | Bambara |
|-----|---------|-----|---------|
| Monday | Tɛnɛn | Friday | Juma |
| Tuesday | Tarata | Saturday | Sibiri |
| Wednesday | Araba | Sunday | Kari |
| Thursday | Alamisa | | |

### Months of the Year

| Month | Bambara | Month | Bambara |
|-------|---------|-------|---------|
| January | Zanwuye | July | Zuluye |
| February | Feburuye | August | Uti |
| March | Marsi | September | Sɛtanburu |
| April | Awirili | October | Oktɔburu |
| May | Mɛ | November | Nɔwanburu |
| June | Zuwen | December | Desanburu |



---

## Time Normalization

The normalizer supports bidirectional time and duration conversion between standard formats and Bambara expressions (TN/ITN).

### With Normalizer
```python
from bambara_normalizer import normalize

normalize("A nana 7:30 la", expand_times=True)   # => "a nana nɛgɛ kaɲɛ wolonwula ni sanga bi saba la"
normalize("A nana 7:30 la", expand_times=False)  # => "a nana 7:30 la"

# WER preset has expand_times=True by default
normalize("A nana 13:50 la", preset="wer")  # => "a nana nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru la"
```

### Clock Time to Bambara (Text Normalization)
```python
from bambara_normalizer import time_to_bambara, format_time_bambara, normalize_times_in_text
from datetime import time

# Clock times
time_to_bambara(1, 0)       # => "Nɛgɛ kaɲɛ kelen"
time_to_bambara(1, 5)       # => "Nɛgɛ kaɲɛ kelen ni sanga duuru"
time_to_bambara(7, 30)      # => "Nɛgɛ kaɲɛ wolonwula  ni sanga bi saba"
time_to_bambara(13, 50)     # => "Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru"

# From time object or string
format_time_bambara(time(7, 30))  # => "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"
format_time_bambara("13:50")      # => "Nɛgɛ kaɲɛ tan ni sab ni sanga bi duuru"

# In text
normalize_times_in_text("A nana 7:30 la")  # => "A nana nɛgɛ kaɲɛ wolonwula ni sanga bi saba la"
```

### Bambara to Clock Time (Inverse Text Normalization)
```python
from bambara_normalizer import bambara_to_time

bambara_to_time("Nɛgɛ kaɲɛ kelen")
# => datetime.time(1, 0)

bambara_to_time("Nɛgɛ kaɲɛ wolonwula ni sanga bi saba")
# => datetime.time(7, 30)
```

### Duration to Bambara
```python
from bambara_normalizer import duration_to_bambara, format_duration_bambara

# Durations
duration_to_bambara(minutes=30)                      # => "miniti bi saba"
duration_to_bambara(hours=1, minutes=30)             # => "lɛrɛ kelen ni miniti bi saba"
duration_to_bambara(hours=1, minutes=30, seconds=10) # => "lɛrɛ kelen ni miniti bi saba ni segɔni tan"

# From string format
format_duration_bambara("30min")      # => "miniti bi saba"
format_duration_bambara("1h30min")    # => "lɛrɛ kelen ni miniti bi saba"
format_duration_bambara("1h30min10s") # => "lɛrɛ kelen ni miniti bi saba ni segɔni tan"
```

### Bambara to Duration (Inverse Text Normalization)
```python
from bambara_normalizer import bambara_to_duration

bambara_to_duration("miniti bi saba")
# => (0, 30, 0)  # (hours, minutes, seconds)

bambara_to_duration("lɛrɛ kelen ni miniti bi saba")
# => (1, 30, 0)

bambara_to_duration("lɛrɛ kelen ni miniti bi saba ni segɔni tan")
# => (1, 30, 10)
```

### Time Format

Clock time follows this structure:
```
Nɛgɛ kaɲɛ [hour] ( ni sanga [minutes])
```

Example: **7:30** => `Nɛgɛ kaɲɛ wolonwula ni sanga bi saba`

Literal translation: "Clock needle seven passed with minute thirty"

Duration follows this structure:
```
(lɛrɛ [hours] ni) (miniti [minutes] ni) (segɔni [seconds])
```

Example: **1h30min10s** => `lɛrɛ kelen ni miniti bi saba ni segɔni tan`

---

## Measurement Normalization

The normalizer supports bidirectional measurement conversion between standard units and Bambara expressions (TN/ITN).

### With Normalizer
```python
from bambara_normalizer import normalize

normalize("A ye 5 kg san", expand_measurements=True)   # => "a ye kilogaramu duuru san"
normalize("A ye 5 kg san", expand_measurements=False)  # => "a ye 5 kg san"

# WER preset has expand_measurements=True by default
normalize("So in bɛ 100 m", preset="wer")  # => "so in bɛ mɛtɛrɛ kɛmɛ"
```

### Measurement to Bambara (Text Normalization)
```python
from bambara_normalizer import measurement_to_bambara, format_measurement_bambara, normalize_measurements_in_text

# Weight
measurement_to_bambara(5, "kg")      # => "kilogaramu duuru"
measurement_to_bambara(100, "g")     # => "garamu kɛmɛ"

# Length
measurement_to_bambara(10, "km")     # => "kilomɛtɛrɛ tan"
measurement_to_bambara(100, "m")     # => "mɛtɛrɛ kɛmɛ"
measurement_to_bambara(50, "cm")     # => "santimɛtɛrɛ bi duuru"

# Volume
measurement_to_bambara(2, "L")       # => "litiri fila"
measurement_to_bambara(500, "mL")    # => "mililitiri kɛmɛ duuru"

# Area
measurement_to_bambara(3, "ha")      # => "ɛkitari saba"
measurement_to_bambara(100, "m²")    # => "mɛtɛrɛ kare kɛmɛ"

# Decimal values
measurement_to_bambara(2.5, "L")     # => "litiri fila tomi duuru"

# From string format
format_measurement_bambara("5kg")    # => "kilogaramu duuru"
format_measurement_bambara("100 m")  # => "mɛtɛrɛ kɛmɛ"

# In text
normalize_measurements_in_text("A ye 5 kg san")  # => "A ye kilogaramu duuru san"
normalize_measurements_in_text("So in bɛ 100 m") # => "So in bɛ mɛtɛrɛ kɛmɛ"
```

### Bambara to Measurement (Inverse Text Normalization)
```python
from bambara_normalizer import bambara_to_measurement, denormalize_measurements_in_text

bambara_to_measurement("kilogaramu duuru")
# => (5, 'kg')

bambara_to_measurement("mɛtɛrɛ kɛmɛ")
# => (100, 'm')

bambara_to_measurement("litiri fila tomi duuru")
# => (2.5, 'L')

# In text
denormalize_measurements_in_text("A ye kilogaramu duuru san")
# => "A ye 5 kg san"
```

### Measurement Format

Measurements follow this structure:
```
[unit] [number]
```

Example: **5 kg** => `kilogaramu duuru`

Literal translation: "kilogram five"

### Supported Units

#### Weight
| Unit | Abbreviation | Bambara |
|------|--------------|---------|
| Kilogram | kg | kilogaramu |
| Gram | g | garamu |
| Milligram | mg | miligaramu |
| Ton | t | tɔni |

#### Length
| Unit | Abbreviation | Bambara |
|------|--------------|---------|
| Kilometer | km | kilomɛtɛrɛ |
| Meter | m | mɛtɛrɛ |
| Centimeter | cm | santimɛtɛrɛ |
| Millimeter | mm | milimɛtɛrɛ |

#### Volume
| Unit | Abbreviation | Bambara |
|------|--------------|---------|
| Liter | L | litiri |
| Milliliter | mL | mililitiri |

#### Area
| Unit | Abbreviation | Bambara |
|------|--------------|---------|
| Hectare | ha | ɛkitari |
| Square meter | m² | mɛtɛrɛ kare |

---

## Numeric Expansion (dates, times, measurements, numbers)

Dates, times, measurements and bare numbers all compete for the same digits. The normalizer resolves them in a **single classification pass**: every numeric span of the text is claimed by exactly one kind, and only then is anything rewritten. Expansion therefore does not depend on the order the expanders run in.

Precedence runs from the most specific shape to the most generic:

```
date > time > measurement > number
```

```python
from bambara_normalizer import find_numeric_spans, normalize_numeric_expressions

text = "Ne taara sugu la 24-12-2025 la, 10:45 waati, ne ye tulu 6 l san ani sukaro 10 kg."

[(s.source, s.kind) for s in find_numeric_spans(text)]
# => [('24-12-2025', 'date'), ('10:45', 'time'), ('6 l', 'measurement'), ('10 kg', 'measurement')]

normalize_numeric_expressions(text)
# => "Ne taara sugu la Desanburu tile mugan ni naani san baa fila ni mugan ni duuru la, ..."
```

A span keeps its kind whether or not that kind is enabled, so partial configurations are safe: disabling one expander never lets another one mis-read its digits.

```python
# expand_numbers=True, expand_dates=False: the date is left alone, not split into three numbers
normalize_numeric_expressions("A bɛ 24-12-2025 la ni 3", dates=False)
# => "A bɛ 24-12-2025 la ni saba"

normalize("A bɛ 24-12-2025 la ni 3", expand_numbers=True, expand_dates=False, remove_punctuation=False)
# => "a bɛ 24-12-2025 la ni saba"
```

The single-kind functions (`normalize_dates_in_text`, `normalize_times_in_text`, `normalize_measurements_in_text`, `normalize_numbers_in_text`) each expand only their own shape and are unaware of the others — `normalize_numbers_in_text` will happily expand the digits of a date. Use `normalize_numeric_expressions` (or the normalizer, which calls it) for mixed text.

**Not resolved by precedence:** genuinely ambiguous shapes. `10-45` could be a date fragment or a ratio, and `24-12-2025` is read as DD-MM-YYYY, never MM-DD-YYYY. Precedence makes the choice *deterministic and documented*, not correct in every context.

## ASR Evaluation Framework

### Quick Evaluation

```python
from bambara_normalizer import evaluate


result = evaluate(
    reference="B'a fɔ ka taa",
    hypothesis="bɛ a fɔ ka taa"

)

print(f"WER: {result.wer:.2%}")  
print(f"CER: {result.cer:.2%}")
print(f"MER: {result.mer:.2%}")
```

### Evaluator with Mode Selection

> [!IMPORTANT]
> The `mode` parameter determines how contractions are handled during evaluation. This significantly impacts WER scores when reference and hypothesis use different orthographic conventions.

```python
from bambara_normalizer import evaluate


result = evaluate(
    reference="k'a ta", 
    hypothesis="ka a ta"
    mode="expand" # contract | preserve 
    )
print(f"WER: {result.wer:.2%}")   
```

### Flexible Configuration

For full control use the evalution class and define the normalization configuration:

```python
from bambara_normalizer import (
    BambaraNormalizer, 
    BambaraNormalizerConfig, 
    BambaraEvaluator
)

# Define custom normalizer: same then the config we did upside
config = BambaraNormalizerConfig(
    contraction_mode="contract",
    preserve_tones=False,
    lowercase=True,
    remove_punctuation=True,
    normalize_legacy_orthography=True,
)


evaluator = BambaraEvaluator(config=config)


result = evaluator.evaluate(
    reference="K'a fɔ́!",
    hypothesis="ka a fo"
)
print(f"WER: {result.wer:.2%}")
```

### Batch Evaluation

```python
from bambara_normalizer import BambaraEvaluator

evaluator = BambaraEvaluator(mode="contract")

references = ["k'a ta", "b'a fɔ", "n'a ma"]
hypotheses = ["ka a ta", "bɛ a fɔ", "na a ma"]

aggregate, individual = evaluator.evaluate_batch(references, hypotheses)

print(f"Overall WER: {aggregate.wer:.2%}")
for i, result in enumerate(individual):
    print(f"  [{i}] WER: {result.wer:.2%}")
```

### Available Metrics

| Metric | Method | Description |
|--------|--------|-------------|
| **WER** | `evaluator.wer(ref, hyp)` | Word Error Rate |
| **CER** | `evaluator.cer(ref, hyp)` | Character Error Rate |
| **MER** | `evaluator.mer(ref, hyp)` | Match Error Rate |
| **WIL** | `evaluator.wil(ref, hyp)` | Word Information Lost |
| **WIP** | `evaluator.wip(ref, hyp)` | Word Information Preserved |
| **DER** | `result.der` | Diacritic Error Rate (tone accuracy) |

---

## Contraction Modes

> [!WARNING]
> Choosing the right mode is critical for fair ASR evaluation. Using the wrong mode can inflate or deflate WER scores artificially.

Version 2.0 introduces **three contraction modes** to handle bidirectional Bambara orthography:

| Mode | Direction | When to Use |
|------|-----------|-------------|
| `expand` | `b'a` => `bɛ a` | Default. Full linguistic analysis with k'/n' disambiguation |
| `contract` | `bɛ a` => `b'a` | Simpler, more forgiving. No disambiguation ambiguity |
| `preserve` | No change | Debugging, or when you want raw comparison |

### Why Contract Mode Matters

**Expansion is complex**  the contraction `k'` can expand to three different words:

| Contraction | Possible Expansions | Meaning |
|-------------|---------------------|---------|
| `k'a` | `ka a` | infinitive marker |
| `k'a` | `kɛ a` | verb "to do" |
| `k'a` | `ko a` | verb "to say" |

The normalizer uses context to disambiguate, but some cases are genuinely ambiguous.

**Contraction is simple**  all variants collapse to the same form:

```
ka a  ─┐
kɛ a  ─┼─>  k'a
ko a  ─┘
```

> [!TIP]
> For ASR evaluation, **contract mode is more forgiving** because it doesn't penalize the model for disambiguation differences when both forms are linguistically valid.

### Contraction Mappings

| Expanded | Contracted | Function |
|----------|------------|----------|
| `bɛ` + vowel | `b'` | Affirmative imperfective |
| `tɛ` + vowel | `t'` | Negative imperfective |
| `ye` + vowel | `y'` | Perfective marker |
| `ni` + vowel | `n'` | Conjunction |
| `na` + vowel | `n'` | Verb "come" |
| `ka` + vowel | `k'` | Infinitive marker |
| `kɛ` + vowel | `k'` | Verb "to do" |
| `ko` + vowel | `k'` | Verb "to say" |

---

## Command Line Interface

The CLI is built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/):
`--help` is fully formatted, evaluation metrics come back as tables, and results printed to a
terminal are framed. Piped or redirected output is always plain text, so the tool composes with
other commands; `--plain` forces plain text on a terminal too.

### Basic Usage

```bash

# default mode is expand
bambara-normalize "B'a fɔ́"
# Output: bɛ a fɔ

# Contract mode
bambara-normalize --mode contract "bɛ a fɔ"
# Output: b'a fɔ

# Preserve mode
bambara-normalize --mode preserve "B'a fɔ"
# Output: b'a fɔ
```

### With Presets

```bash
# WER preset (aggressive normalization)
bambara-normalize --preset wer "K'a fɔ́!"
# Output: ka a fɔ

# WER preset with contract mode
bambara-normalize --preset wer --mode contract "Ka a fɔ"
# Output: k'a fɔ

# CER preset
bambara-normalize --preset cer "B'a fɔ"
```

### File Evaluation

```bash
# Evaluate reference vs hypothesis files
bambara-normalize --evaluate reference.txt hypothesis.txt

# With contract mode
bambara-normalize --evaluate --mode contract ref.txt hyp.txt

# Output detailed metrics
bambara-normalize --evaluate --detailed ref.txt hyp.txt
```

### Batch Processing

```bash
# Process file line by line
bambara-normalize --input corpus.txt --output normalized.txt

# With specific mode
bambara-normalize --input corpus.txt --output normalized.txt --mode contract

# Read from stdin
echo "B'a fɔ́" | bambara-normalize
```

### Options

| Option | Description |
|--------|-------------|
| `-m, --mode` | `expand` (default), `contract`, `preserve` |
| `-p, --preset` | `standard` (default), `wer`, `cer`, `minimal`, `preserving_tones` |
| `-f, --input` | Input file, one utterance per line (alias: `--file`) |
| `-o, --output` | Write results to a file instead of stdout |
| `-e, --evaluate` | Treat the two arguments as reference and hypothesis files |
| `--detailed` | With `--evaluate`, add a per-utterance table |
| `--preserve-tones` | Keep tone marks |
| `--expand-numbers` | Expand digits to Bambara words |
| `--debug` | Print the intermediate normalization steps to stderr |
| `--plain` | Unstyled output, even on a terminal |
| `-v, --version` | Print the version |
| `-h, --help` | Show help |

---

## Linguistic Decisions

### Why Normalize?

Bambara orthography allows variation. For the same spoken utterance:
- Annotator A writes: `k'a ta`
- Annotator B writes: `ka a ta`

**Both are correct.** Without normalization, we penalize models for human writing inconsistencies, not recognition errors.

### n' Disambiguation

| Pattern | Expansion | Meaning |
|---------|-----------|---------|
| `n' + pronoun + ma` | `na` | Verb "to come" |
| `n' + other` | `ni` | Conjunction (default) |

**Examples:**
- `n'a ma` => `na a ma` (come to him)
- `n'a ta` => `ni a ta` (if he takes)

### k' Disambiguation Rules

Applied in priority order (derived from [Daba grammar](https://github.com/maslinych/daba)):

| Priority | Pattern | Result | Example |
|----------|---------|--------|---------|
| 1 | `k' + pronoun + ma + X + ye` | `kɛ` | `k'a ma hɛrɛ ye` => `kɛ a ma hɛrɛ ye` |
| 2 | `k' + pronoun + ma +` speech marker | `ko` | `k'anw ma ko` => `ko anw ma ko` |
| 3 | `k' + pronoun +` postposition | `kɛ` | `k'a la` => `kɛ a la` |
| 4 | `k' + pronoun +` clause marker | `ko` | `k'an ka ta` => `ko an ka ta` |
| 5 | Default | `ka` | `k'a ta` => `ka a ta` |

**Postpositions:** `la`, `na`, `ye`, `fɛ`, `kɔnɔ`, `kɔ`, `kɔrɔ`, `kan`, `kun`, `ɲɛ`, `bolo`

**Clause markers:** `ka`, `kana`, `bɛ`, `tɛ`, `bɛna`, `tɛna`, `tun`, `mana`

### Legacy Orthography Conversion

| Legacy | Modern | Notes |
|--------|--------|-------|
| `è` | `ɛ` | Pre-standard spelling |
| `ò` | `ɔ` | Pre-standard spelling |
| `ny` | `ɲ` | Digraph => single character |
| `ng` | `ŋ` | Digraph => single character |
| `ñ` | `ɲ` | Spanish/Senegalese variant |

---

## Known Limitations

### Inherent Linguistic Ambiguity

> [!CAUTION]
> Some Bambara constructions are **genuinely ambiguous** and cannot be resolved without broader context. This is not a bug  it reflects real ambiguity in the language.

#### The `ye` Problem

The word `ye` has **five** grammatical functions:

| Function | Example | Meaning |
|----------|---------|---------|
| Postposition | `à fɔ́ ń yé` | say it **to** me |
| Perfective | `ù ye ɲɔ̀ gòsi` | they **have** beaten |
| Copula | `ò yé kɔ̀nɔ yé` | it **is** a bird |
| Verb "see" | `ka a ye` | **to see** it |
| Imperative | `á' yé nà!` | come! (plural) |

This creates genuine ambiguity for `k'a ye`:

| Interpretation | Expansion | Meaning |
|----------------|-----------|---------|
| Postposition | `kɛ a ye` | do it for him |
| Verb "see" | `ka a ye` | to see it |

**Default behavior:** The normalizer chooses `kɛ a ye` (postposition is more frequent).

**Solution:** Use `mode="contract"` for ASR evaluation to avoid disambiguation penalties:

```python
evaluator = BambaraEvaluator(mode="contract")
# Both "kɛ a ye" and "ka a ye" => "k'a ye" 
```

### Scope

The normalizer uses **local context** (1-3 word lookahead). It does not:
- Parse full sentence structure
- Use dictionary/lexicon for POS tagging
- Consider discourse-level context

---

## Utility Functions

```python
from bambara_normalizer import (
    is_contraction,
    can_contract,
    find_contractions,
    find_contractable_sequences,
    compare_normalization_modes,
    analyze_text,
    is_bambara_vowel,
    get_tone,
    remove_tones,
    number_to_bambara,
    bambara_to_number,
    normalize_numbers_in_text,
    denormalize_numbers_in_text,
    is_number_word,
    
    bambara_to_date,
    bambara_to_day_of_week,
    bambara_to_month,
    date_to_bambara,
    day_of_week_to_bambara,
    denormalize_dates_in_text,
    format_date_bambara,
    is_bambara_day,
    is_bambara_month,
    month_to_bambara,
    normalize_dates_in_text,

    time_to_bambara,
    bambara_to_time,
    format_time_bambara,
    duration_to_bambara,
    bambara_to_duration,
    format_duration_bambara,
    normalize_times_in_text,
    is_time_word,

    measurement_to_bambara,
    bambara_to_measurement,
    format_measurement_bambara,
    normalize_measurements_in_text,
    denormalize_measurements_in_text,
    is_measurement_word,
    get_unit_category,
)


is_contraction("b'a")                   
is_contraction("bɛ")                     
can_contract("bɛ a")                      

# Find patterns in text
find_contractions("B'a fɔ k'a ta")       # ["b'", "k'"]
find_contractable_sequences("bɛ a fɔ")   # [('bɛ', 'a')]

# Compare modes side-by-side
compare_normalization_modes("b'a fɔ")
# {'original': "b'a fɔ", 'expand': 'bɛ a fɔ', 'contract': "b'a fɔ", 'preserve': "b'a fɔ"}

# Full text analysis
analyze_text("B'a fɔ k'a la")
# {'word_count': 4, 'contractions_found': ["b'", "k'"], 'has_tone_marks': False, ...}

# Tone handling
get_tone("fɔ́")                           # "high"
remove_tones("fɔ́ bɛ̀")                    # "fɔ bɛ"

# Number conversion: digits => Bambara words
number_to_bambara(5)                     # "duuru"
number_to_bambara(23)                    # "mugan ni saba"
number_to_bambara(100)                   # "kɛmɛ"
number_to_bambara(123)                   # "kɛmɛ ni mugan ni saba"
number_to_bambara(1000)                  # "waa kelen"
number_to_bambara(5.3)                   # "duuru tomi saba"

# Number conversion: Bambara words => digits
bambara_to_number("duuru")               # 5
bambara_to_number("mugan ni saba")       # 23
bambara_to_number("kɛmɛ")                # 100
bambara_to_number("waa kelen")           # 1000
bambara_to_number("duuru tomi saba")     # 5.3

# Number normalization in text
normalize_numbers_in_text("A ye 5 di")       # "A ye duuru  di"
normalize_numbers_in_text("Mɔgɔ 100 nana")        # "Mɔgɔ kɛmɛ nana"
normalize_numbers_in_text("A be san 25 bɔ")       # "A be san mugan ni duuru bɔ"

# Inverse: Bambara words => digits in text
denormalize_numbers_in_text("A ye duuru di")  # "A ye 5  di"
denormalize_numbers_in_text("Mɔgɔ kɛmɛ nana")      # "Mɔgɔ 100 nana"

# Check if word is a number word
is_number_word("duuru")                  # True
is_number_word("kɛmɛ")                   # True
is_number_word("fɔ")                     # False


# Date conversion: dates => Bambara
date_to_bambara(2024, 10, 13)            # "Oktɔburu tile tan ni saba san baa fila ni mugan ni naani"
format_date_bambara("13-10-2024")        # Same as above

# Date conversion: Bambara => dates
bambara_to_date("Oktɔburu tile tan ni saba san baa fila ni mugan ni naani")  # datetime.date(2024, 10, 13)

# Day/Month helpers
day_of_week_to_bambara(0)                # "Tɛnɛn" (Monday)
day_of_week_to_bambara(6)                # "Kari" (Sunday)
month_to_bambara(10)                     # "Oktɔburu"
bambara_to_month("Oktɔburu")             # 10

# Date normalization in text
normalize_dates_in_text("A bɛ na 13-10-2024 la")  # "A bɛ na Oktɔburu tile ... la"

# Check if word is date-related
is_bambara_month("Oktɔburu")             # True
is_bambara_day("Juma")                   # True


# Time conversion: clock times → Bambara
time_to_bambara(1, 0)                    # "Nɛgɛ kaɲɛ kelen"
time_to_bambara(7, 30)                   # "Nɛgɛ kaɲɛ wolonwula ni sanga bi saba"
format_time_bambara("13:50")             # "Nɛgɛ kaɲɛ tan ni saba ni sanga bi duuru"

# Time conversion: Bambara → clock times
bambara_to_time("Nɛgɛ kaɲɛ wolonwula ni sanga bi saba")  # datetime.time(7, 30)

# Duration conversion: durations → Bambara
duration_to_bambara(minutes=30)          # "miniti bi saba"
duration_to_bambara(hours=1, minutes=30) # "lɛrɛ kelen ni miniti bi saba"
format_duration_bambara("1h30min10s")    # "lɛrɛ kelen ni miniti bi saba ni segɔni tan"

# Duration conversion: Bambara → durations
bambara_to_duration("lɛrɛ kelen ni miniti bi saba")  # (1, 30, 0)

# Time normalization in text
normalize_times_in_text("A nana 7:30 la")  # "A nana Nɛgɛ kaɲɛ wolonwula ... la"

# Check if word is time-related
is_time_word("lɛrɛ")                      # True
is_time_word("miniti")                    # True
is_time_word("segɔni")                    # True



# Measurement conversion: units => Bambara
measurement_to_bambara(5, "kg")          # "kilogaramu duuru"
measurement_to_bambara(100, "m")         # "mɛtɛrɛ kɛmɛ"
measurement_to_bambara(2.5, "L")         # "litiri fila tomi duuru"
format_measurement_bambara("5kg")        # "kilogaramu duuru"

# Measurement conversion: Bambara => units
bambara_to_measurement("kilogaramu duuru")   # (5, 'kg')
bambara_to_measurement("mɛtɛrɛ kɛmɛ")        # (100, 'm')

# Measurement normalization in text
normalize_measurements_in_text("A ye 5 kg san")      # "A ye kilogaramu duuru san"
denormalize_measurements_in_text("kilogaramu duuru") # "5 kg"

# Check if word is measurement-related
is_measurement_word("kilogaramu")        # True
is_measurement_word("mɛtɛrɛ")            # True
get_unit_category("kg")                  # "weight"
get_unit_category("m")                   # "length"
```


---

## Evaluation Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| **WER** | Word Error Rate | 0.0 – ∞ |
| **CER** | Character Error Rate | 0.0 – ∞ |
| **MER** | Match Error Rate | 0.0 – 1.0 |
| **WIL** | Word Information Lost | 0.0 – 1.0 |
| **WIP** | Word Information Preserved | 0.0 – 1.0 |
| **DER** | Diacritic Error Rate (tone accuracy) | 0.0 – ∞ |

---



## References

#### Linguistic Resources
- [Bambara Reference Corpus](http://cormand.huma-num.fr/)  Primary corpus
- [Daba Morphological Analyzer](https://github.com/maslinych/daba)  Grammar rules
- [Bamadaba Dictionary](http://cormand.huma-num.fr/bamadaba.html)  Lexical database
- DNAFLA / AMALAN  Bambara standardization body

#### Standards
- UNESCO Bamako Meeting (1966)
- Niamey African Reference Alphabet (1978)

#### Tools
- [jiwer](https://github.com/jitsi/jiwer)  ASR evaluation metrics

#### Related Work
- [NVIDIA NeMo Text Normalization](https://github.com/NVIDIA/NeMo)
- [NeMo TN/ITN Documentation](https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/stable/nlp/text_normalization/wfst/wfst_text_normalization.html)

---

<p align="center">
    <a href="https://github.com/MALIBA-AI">MALIBA-AI</a>
</p>

from bambara_normalizer import (
    bambara_to_number,
    denormalize_numbers_in_text,
    normalize,
    normalize_numbers_in_text,
    number_to_bambara,
)


class TestNumberToBambara:
    def test_units(self):
        assert number_to_bambara(0) == "fu"
        assert number_to_bambara(1) == "kelen"
        assert number_to_bambara(5) == "duuru"
        assert number_to_bambara(9) == "kɔnɔntɔn"

    def test_tens(self):
        assert number_to_bambara(10) == "tan"
        assert number_to_bambara(15) == "tan ni duuru"
        assert number_to_bambara(20) == "mugan"
        assert number_to_bambara(25) == "mugan ni duuru"

    def test_hundreds(self):
        assert number_to_bambara(100) == "kɛmɛ"
        assert number_to_bambara(123) == "kɛmɛ ni mugan ni saba"
        assert number_to_bambara(200) == "kɛmɛ fila"
        assert number_to_bambara(500) == "kɛmɛ duuru"

    def test_thousands(self):
        assert number_to_bambara(1000) == "waa kelen"
        assert number_to_bambara(5000) == "waa duuru"
        assert number_to_bambara(10000) == "waa tan"

    def test_millions(self):
        assert number_to_bambara(1000000) == "miliyɔn kelen"

    def test_decimal(self):
        assert number_to_bambara(5.3) == "duuru tomi saba"


class TestBambaraToNumber:
    def test_units(self):
        assert bambara_to_number("fu") == 0
        assert bambara_to_number("kelen") == 1
        assert bambara_to_number("duuru") == 5

    def test_compound(self):
        assert bambara_to_number("tan ni duuru") == 15
        assert bambara_to_number("kɛmɛ ni mugan ni saba") == 123
        assert bambara_to_number("waa kelen") == 1000

    def test_decimal(self):
        assert bambara_to_number("duuru tomi saba") == 5.3


class TestNumberTextNormalization:
    def test_normalize_numbers_in_text(self):
        assert normalize_numbers_in_text("A ye 5 wari di") == "A ye duuru wari di"
        assert normalize_numbers_in_text("Mɔgɔ 100 nana") == "Mɔgɔ kɛmɛ nana"

    def test_denormalize_numbers_in_text(self):
        assert denormalize_numbers_in_text("A ye duuru wari di") == "A ye 5 wari di"
        assert denormalize_numbers_in_text("Mɔgɔ kɛmɛ nana") == "Mɔgɔ 100 nana"

    def test_trailing_punctuation_is_not_a_decimal_separator(self):
        assert normalize_numbers_in_text("Ne wolo la san 2020.") == (
            "Ne wolo la san waa fila ni mugan."
        )
        assert normalize_numbers_in_text("A ye 42, 43 di") == (
            "A ye bi naani ni fila, bi naani ni saba di"
        )

    def test_separator_between_digits_is_kept(self):
        assert normalize_numbers_in_text("A ye 3.5 di") == "A ye saba tomi duuru di"
        assert normalize_numbers_in_text("Mɔgɔ 1,000 nana") == "Mɔgɔ waa kelen nana"


class TestNumberNormalizerIntegration:
    def test_with_expand_numbers(self):
        result = normalize("A ye 5 wari di", expand_numbers=True)
        assert "duuru" in result
        assert "5" not in result

    def test_without_expand_numbers(self):
        result = normalize("A ye 5 wari di", expand_numbers=False)
        assert "5" in result
        assert "duuru" not in result

    def test_wer_preset_expands_numbers(self, wer_normalizer):
        result = wer_normalizer("A ye 100 sɔrɔ")
        assert "kɛmɛ" in result


class TestNumberRoundTrip:
    def test_round_trip_conversion(self):
        test_numbers = [0, 1, 5, 10, 15, 20, 42, 100, 123, 500, 1000, 5000]
        for n in test_numbers:
            bambara = number_to_bambara(n)
            back = bambara_to_number(bambara)
            assert back == n, f"Round trip failed for {n}: {bambara} -> {back}"

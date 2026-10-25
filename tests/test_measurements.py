"""Measurement normalization tests."""

import pytest

from bambara_normalizer import (
    BambaraNormalizer,
    BambaraNormalizerConfig,
    bambara_to_measurement,
    denormalize_measurements_in_text,
    format_measurement_bambara,
    get_unit_category,
    is_measurement_word,
    measurement_to_bambara,
    normalize,
    normalize_measurements_in_text,
)


class TestMeasurementToBambara:
    def test_weight_kg(self):
        assert measurement_to_bambara(5, "kg") == "kilogaramu duuru"

    def test_weight_g(self):
        assert measurement_to_bambara(100, "g") == "garamu kɛmɛ"

    def test_weight_ton(self):
        assert measurement_to_bambara(2, "t") == "tɔni fila"

    def test_length_km(self):
        assert measurement_to_bambara(10, "km") == "kilomɛtɛrɛ tan"

    def test_length_m(self):
        assert measurement_to_bambara(100, "m") == "mɛtɛrɛ kɛmɛ"

    def test_length_cm(self):
        assert measurement_to_bambara(50, "cm") == "santimɛtɛrɛ bi duuru"

    def test_length_mm(self):
        assert measurement_to_bambara(5, "mm") == "milimɛtɛrɛ duuru"

    def test_volume_L(self):  # noqa: N802
        assert measurement_to_bambara(2, "L") == "litiri fila"

    def test_volume_mL(self):  # noqa: N802
        assert measurement_to_bambara(500, "mL") == "mililitiri kɛmɛ duuru"

    def test_area_ha(self):
        assert measurement_to_bambara(3, "ha") == "ɛkitari saba"

    def test_area_m2(self):
        assert measurement_to_bambara(100, "m²") == "mɛtɛrɛ kare kɛmɛ"

    def test_decimal_value(self):
        assert measurement_to_bambara(2.5, "L") == "litiri fila tomi duuru"

    def test_full_word_kilogram(self):
        assert measurement_to_bambara(5, "kilogram") == "kilogaramu duuru"

    def test_full_word_meter(self):
        assert measurement_to_bambara(100, "meter") == "mɛtɛrɛ kɛmɛ"

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            measurement_to_bambara(5, "xyz")


class TestBambaraToMeasurement:
    def test_weight_kg(self):
        assert bambara_to_measurement("kilogaramu duuru") == (5, "kg")

    def test_weight_g(self):
        assert bambara_to_measurement("garamu kɛmɛ") == (100, "g")

    def test_length_km(self):
        assert bambara_to_measurement("kilomɛtɛrɛ tan") == (10, "km")

    def test_length_m(self):
        assert bambara_to_measurement("mɛtɛrɛ kɛmɛ") == (100, "m")

    def test_volume_L(self):  # noqa: N802
        assert bambara_to_measurement("litiri fila") == (2, "L")

    def test_area_m2(self):
        assert bambara_to_measurement("mɛtɛrɛ kare kɛmɛ") == (100, "m²")

    def test_decimal_value(self):
        assert bambara_to_measurement("litiri fila tomi duuru") == (2.5, "L")

    def test_no_unit_raises(self):
        with pytest.raises(ValueError):
            bambara_to_measurement("duuru")


class TestFormatMeasurementBambara:
    def test_5kg(self):
        assert format_measurement_bambara("5kg") == "kilogaramu duuru"

    def test_5_kg_with_space(self):
        assert format_measurement_bambara("5 kg") == "kilogaramu duuru"

    def test_100m(self):
        assert format_measurement_bambara("100m") == "mɛtɛrɛ kɛmɛ"

    def test_2_5l(self):
        assert format_measurement_bambara("2.5L") == "litiri fila tomi duuru"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            format_measurement_bambara("invalid")


class TestNormalizeMeasurementsInText:
    def test_weight_in_sentence(self):
        result = normalize_measurements_in_text("A ye 5 kg san")
        assert result == "A ye kilogaramu duuru san"

    def test_length_in_sentence(self):
        result = normalize_measurements_in_text("So in bɛ 100 m")
        assert result == "So in bɛ mɛtɛrɛ kɛmɛ"

    def test_volume_in_sentence(self):
        result = normalize_measurements_in_text("Ji 2 L")
        assert result == "Ji litiri fila"

    def test_multiple_measurements(self):
        result = normalize_measurements_in_text("5 kg ni 100 m")
        assert "kilogaramu duuru" in result
        assert "mɛtɛrɛ kɛmɛ" in result

    def test_no_space_before_unit(self):
        result = normalize_measurements_in_text("A ye 5kg san")
        assert result == "A ye kilogaramu duuru san"

    def test_decimal_in_text(self):
        result = normalize_measurements_in_text("Ji 2.5 L ye")
        assert "litiri fila tomi duuru" in result


class TestDenormalizeMeasurementsInText:
    def test_weight(self):
        result = denormalize_measurements_in_text("A ye kilogaramu duuru san")
        assert "5 kg" in result

    def test_length(self):
        result = denormalize_measurements_in_text("So in bɛ mɛtɛrɛ kɛmɛ")
        assert "100 m" in result

    def test_volume(self):
        result = denormalize_measurements_in_text("Ji litiri fila")
        assert "2 L" in result


class TestIsMeasurementWord:
    def test_unit_words(self):
        assert is_measurement_word("kilogaramu") is True
        assert is_measurement_word("mɛtɛrɛ") is True
        assert is_measurement_word("litiri") is True
        assert is_measurement_word("ɛkitari") is True

    def test_non_unit_word(self):
        assert is_measurement_word("taa") is False
        assert is_measurement_word("duuru") is False


class TestGetUnitCategory:
    def test_weight(self):
        assert get_unit_category("kg") == "weight"
        assert get_unit_category("kilogaramu") == "weight"

    def test_length(self):
        assert get_unit_category("m") == "length"
        assert get_unit_category("mɛtɛrɛ") == "length"

    def test_volume(self):
        assert get_unit_category("L") == "volume"
        assert get_unit_category("litiri") == "volume"

    def test_area(self):
        assert get_unit_category("ha") == "area"
        assert get_unit_category("m²") == "area"

    def test_unknown(self):
        assert get_unit_category("xyz") is None


class TestMeasurementNormalizerIntegration:
    def test_with_expand_measurements(self):
        result = normalize("A ye 5 kg san", expand_measurements=True)
        assert "kilogaramu duuru" in result
        assert "5 kg" not in result

    def test_without_expand_measurements(self):
        result = normalize("A ye 5 kg san", expand_measurements=False)
        assert "5" in result
        assert "kilogaramu" not in result

    def test_wer_preset_expands_measurements(self):
        config = BambaraNormalizerConfig.for_wer_evaluation()
        normalizer = BambaraNormalizer(config)
        result = normalizer("A ye 5 kg san")
        assert "kilogaramu" in result


class TestMeasurementRoundTrip:
    def test_weight(self):
        original = (5, "kg")
        bambara = measurement_to_bambara(*original)
        back = bambara_to_measurement(bambara)
        assert back == original

    def test_length(self):
        original = (100, "m")
        bambara = measurement_to_bambara(*original)
        back = bambara_to_measurement(bambara)
        assert back == original

    def test_volume(self):
        original = (2, "L")
        bambara = measurement_to_bambara(*original)
        back = bambara_to_measurement(bambara)
        assert back == original

    def test_decimal(self):
        original = (2.5, "L")
        bambara = measurement_to_bambara(*original)
        back = bambara_to_measurement(bambara)
        assert back == original

    def test_multiple_units(self):
        test_cases = [
            (5, "kg"),
            (100, "g"),
            (10, "km"),
            (50, "cm"),
            (500, "mL"),
            (3, "ha"),
        ]
        for original in test_cases:
            bambara = measurement_to_bambara(*original)
            back = bambara_to_measurement(bambara)
            assert back == original, f"Round trip failed for {original}"


class TestGroupedMeasurementValue:
    def test_space_grouped_value(self):
        assert normalize_measurements_in_text("malo 1 000 kg") == "malo kilogaramu waa kelen"

    def test_space_grouped_value_with_decimal(self):
        assert normalize_measurements_in_text("A ye 1 000,5 kg") == (
            "A ye kilogaramu waa kelen tomi duuru"
        )

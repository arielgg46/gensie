from gensie.runtime import normalize_model_output_strings


def test_normalize_model_output_strings_decodes_literal_unicode_escapes():
    value = {
        "title": "El Quijote",
        "evidence": "lengua original: \\u0065spa\\u00f1ol",
        "items": ["cafe\u0301", "nin\\u0303o"],
    }

    assert normalize_model_output_strings(value) == {
        "title": "El Quijote",
        "evidence": "lengua original: español",
        "items": ["café", "niño"],
    }


def test_normalize_model_output_strings_keeps_object_keys_unchanged():
    value = {"cafe\u0301": "\\u0063af\\u00e9"}

    assert normalize_model_output_strings(value) == {"cafe\u0301": "café"}


def test_normalize_model_output_strings_does_not_create_control_characters():
    assert normalize_model_output_strings("\\u00101") == "\\u00101"

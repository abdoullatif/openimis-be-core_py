from django.test import SimpleTestCase

from core.custom_filters.filter_condition_utils import (
    extract_custom_filters_from_json_ext,
    parse_custom_filter_part,
)


class FilterConditionUtilsTest(SimpleTestCase):
    def test_parse_string_icontains(self):
        path, value_type, raw = parse_custom_filter_part("region__icontains=Conakry")
        self.assertEqual(path, "region__icontains")
        self.assertEqual(value_type, "string")
        self.assertEqual(raw, "Conakry")

    def test_parse_string_boolean_legacy(self):
        path, value_type, raw = parse_custom_filter_part("able_bodied__boolean=False")
        self.assertEqual(path, "able_bodied")
        self.assertEqual(value_type, "boolean")
        self.assertEqual(raw, "False")

    def test_parse_dict(self):
        path, value_type, raw = parse_custom_filter_part(
            {"field": "region", "filter": "icontains", "value": "NZER", "type": "string"}
        )
        self.assertEqual(path, "region__icontains")
        self.assertEqual(value_type, "string")
        self.assertEqual(raw, "NZER")

    def test_extract_string_and_dict(self):
        json_ext = {
            "advanced_criteria": [
                {"custom_filter_condition": "region__icontains=NZER"},
                {"field": "type", "filter": "iexact", "value": "beneficiaire", "type": "string"},
            ]
        }
        filters = extract_custom_filters_from_json_ext(json_ext)
        self.assertEqual(len(filters), 2)
        self.assertEqual(filters[0], "region__icontains=NZER")
        self.assertEqual(filters[1]["field"], "type")

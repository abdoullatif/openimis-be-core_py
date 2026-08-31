"""Parsing and extraction of custom filter criteria (payment plan, payroll)."""

from typing import Any, List, Tuple, Union

# Suffixes used as value types in string conditions (legacy: able_bodied__boolean=False).
SCHEMA_VALUE_TYPES = frozenset({
    "boolean",
    "integer",
    "string",
    "date",
    "decimal",
    "numeric",
    "number",
})


def extract_custom_filters_from_json_ext(json_ext: Any) -> List[Union[str, dict]]:
    """
    Extract filter parts from json_ext.advanced_criteria.

    Supports:
    - {"custom_filter_condition": "region__icontains=Conakry"}
    - {"field": "region", "filter": "icontains", "value": "...", "type": "string"}
    """
    if not isinstance(json_ext, dict):
        return []
    by_status = json_ext.get("advanced_criteria_by_status")
    if isinstance(by_status, dict):
        from_status = by_status.get("ACTIVE") or by_status.get("active")
        if isinstance(from_status, list):
            filters = _extract_from_criteria_list(from_status)
            if filters:
                return filters

    advanced = json_ext.get("advanced_criteria")
    if not advanced:
        return []
    if isinstance(advanced, list):
        return _extract_from_criteria_list(advanced)
    if isinstance(advanced, dict):
        filters = []
        for status_filters in advanced.values():
            if isinstance(status_filters, list):
                filters.extend(_extract_from_criteria_list(status_filters))
        return filters
    return []


def _extract_from_criteria_list(criteria_list: list) -> List[Union[str, dict]]:
    filters = []
    for item in criteria_list:
        if not isinstance(item, dict):
            continue
        # Prefer structured field/filter/value so location objects keep their name.
        if item.get("field") and item.get("filter") and item.get("value") not in (None, ""):
            filters.append(item)
        elif item.get("custom_filter_condition"):
            filters.append(item["custom_filter_condition"])
    return filters


def parse_custom_filter_part(filter_part: Union[str, dict]) -> Tuple[str, str, Any]:
    """
    Parse one criterion into (json_ext_field_path, value_type, raw_value).

    json_ext_field_path is used as: json_ext__{json_ext_field_path}
    Examples:
    - "region__icontains=NZER" -> ("region__icontains", "string", "NZER")
    - "able_bodied__boolean=False" -> ("able_bodied", "boolean", "False")
    - dict field/filter/value -> ("region__icontains", "string", "NZER")
    """
    if isinstance(filter_part, dict):
        field_path = f"{filter_part['field']}__{filter_part['filter']}"
        value_type = filter_part.get("type") or "string"
        return field_path, value_type, filter_part.get("value")

    field_part, raw_value = filter_part.split("=", 1)
    field_name, suffix = field_part.rsplit("__", 1)
    if suffix in SCHEMA_VALUE_TYPES:
        return field_name, suffix, raw_value
    return f"{field_name}__{suffix}", "string", raw_value

"""Small strict validator for the JSON-Schema subset used by this proposal.

Not a general JSON Schema engine. Unknown keywords are rejected when loading a contract;
integration should use CM's existing schema validator instead of a second one.
"""
from __future__ import annotations
import json
import math
import re
from functools import lru_cache
from pathlib import Path

class ValidationError(ValueError):
    pass

@lru_cache(maxsize=16)
def load_schema(name: str):
    if not re.fullmatch(r"[a-z-]+", name):
        raise ValidationError("invalid_contract_name")
    schema = json.loads((Path(__file__).parent / "contracts" / (name + ".schema.json")).read_text())
    _supported(schema)
    return schema

def _supported(rule):
    allowed = {"$schema", "title", "$ref", "$defs", "anyOf", "enum", "type", "properties", "required", "additionalProperties", "items", "maxItems", "minLength", "maxLength", "pattern", "minimum", "maximum"}
    if set(rule) - allowed:
        raise ValidationError("unsupported_schema_keyword")
    for name in ("properties", "$defs"):
        for nested in rule.get(name, {}).values():
            _supported(nested)
    for nested in rule.get("anyOf", []):
        _supported(nested)
    if "items" in rule:
        _supported(rule["items"])


def validate(name: str, value):
    root = load_schema(name)
    _check(root, value, root, "$")
    return value

def _check(rule, value, root, path):
    if "$ref" in rule:
        pointer = rule["$ref"]
        if not pointer.startswith("#/$defs/"):
            raise ValidationError("unsupported_reference")
        return _check(root["$defs"][pointer[8:]], value, root, path)
    if "anyOf" in rule:
        for candidate in rule["anyOf"]:
            try:
                _check(candidate, value, root, path)
                return
            except ValidationError:
                pass
        raise ValidationError(path + ": no matching alternative")
    if "enum" in rule and not any(type(value) is type(x) and value == x for x in rule["enum"]):
        raise ValidationError(path + ": invalid enum")
    kind = rule.get("type")
    tests = {"object":lambda: type(value) is dict,"array":lambda: type(value) is list,
             "string":lambda: type(value) is str,"integer":lambda: type(value) is int,
             "boolean":lambda: type(value) is bool,"null":lambda: value is None}
    if kind and (kind not in tests or not tests[kind]()):
        raise ValidationError(path + ": wrong type")
    if kind == "object":
        props = rule.get("properties", {})
        if any(k not in value for k in rule.get("required", [])):
            raise ValidationError(path + ": missing required field")
        if rule.get("additionalProperties") is False and any(k not in props for k in value):
            raise ValidationError(path + ": unknown field")
        for key, item in value.items():
            if key in props:
                _check(props[key], item, root, path + "." + key)
    elif kind == "array":
        if len(value) > rule.get("maxItems", 100000):
            raise ValidationError(path + ": array too large")
        for i, item in enumerate(value):
            _check(rule["items"], item, root, f"{path}[{i}]")
    elif kind == "string":
        if len(value) < rule.get("minLength", 0) or len(value) > rule.get("maxLength", 1000000):
            raise ValidationError(path + ": invalid string length")
        if "pattern" in rule and re.search(rule["pattern"], value) is None:
            raise ValidationError(path + ": pattern mismatch")
    elif kind == "integer":
        if value < rule.get("minimum", -math.inf) or value > rule.get("maximum", math.inf):
            raise ValidationError(path + ": numeric bound")

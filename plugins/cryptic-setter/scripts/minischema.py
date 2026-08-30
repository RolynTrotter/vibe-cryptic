"""A small JSON Schema validator covering the subset schema/puzzle.schema.json uses.

Pulling in `jsonschema` would be one pip install between a fresh checkout and a
working pipeline, which is exactly the friction this project can't afford. The
subset here is small enough to read in one sitting: type, required, properties,
additionalProperties, enum, const, pattern, items, minItems/minLength,
minimum/maximum, allOf, if/then, and local $ref.
"""

import re

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


class SchemaError(Exception):
    pass


def _resolve(schema, root):
    seen = 0
    while "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise SchemaError(f"only local refs are supported, got {ref!r}")
        target = root
        for part in ref[2:].split("/"):
            target = target[part]
        schema = target
        seen += 1
        if seen > 20:
            raise SchemaError(f"circular $ref at {ref!r}")
    return schema


def _type_ok(value, expected):
    # bool is an int subclass in Python, which would let `true` pass as a number.
    if isinstance(value, bool) and expected in ("integer", "number"):
        return False
    py = _TYPES.get(expected)
    if py is None:
        raise SchemaError(f"unsupported type {expected!r}")
    return isinstance(value, py)


def _matches(schema, value, root):
    """Does value satisfy schema? Used for if/then, so it must not raise."""
    return not validate(value, schema, root=root)


def validate(value, schema, path="$", root=None):
    """Return a list of human-readable error strings; empty means valid."""
    if root is None:
        root = schema
    schema = _resolve(schema, root)
    errors = []

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")

    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, opt) for opt in options):
            got = type(value).__name__
            errors.append(f"{path}: expected {'/'.join(options)}, got {got}")
            return errors  # further checks would be noise

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match /{schema['pattern']}/")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']} characters")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, sub in properties.items():
            if key in value:
                errors += validate(value[key], sub, f"{path}.{key}", root)
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]", root)

    for sub in schema.get("allOf", []):
        sub = _resolve(sub, root)
        if "if" in sub:
            if _matches(sub["if"], value, root) and "then" in sub:
                errors += validate(value, sub["then"], path, root)
        else:
            errors += validate(value, sub, path, root)

    return errors

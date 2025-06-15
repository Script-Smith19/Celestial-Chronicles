import re

def parse_part(part):
    """Parses a field part like 'field' or 'field[3]' into (key, index)."""
    match = re.match(r"(\w+)(?:\[(\w+)\])?", part)
    if not match:
        raise ValueError(f"Invalid field syntax: {part}")
    key = match.group(1)
    index = match.group(2)
    return key, index


def HasField(obj, field_path: str) -> bool:
    """Checks if a nested field path exists in the object."""
    parts = field_path.split('.')
    current = obj

    for i, part in enumerate(parts):
        key, index = parse_part(part)

        # Navigate into dict or attribute
        if isinstance(current, dict):
            if key not in current:
                return False
            current = current[key]
        elif hasattr(current, key):
            current = getattr(current, key)
        else:
            return False

        # Indexing or recursive check for all elements
        if isinstance(current, list):
            if index is not None:
                try:
                    current = current[int(index)]
                except (IndexError, ValueError):
                    return False
            else:
                # Apply remaining path to all elements
                rest = '.'.join(parts[i+1:])
                if not rest:
                    return True  # We're done, the list exists
                return all(HasField(item, rest) for item in current)

        elif isinstance(current, dict):
            if index is not None:
                if index not in current:
                    return False
                current = current[index]
            else:
                # Apply remaining path to all dict values
                rest = '.'.join(parts[i+1:])
                if not rest:
                    return True
                return all(HasField(v, rest) for v in current.values())

        else:
            if index is not None:
                return False  # Can't index into non-collection

    return True

import re

def parse_part(part):
    """Parses a field part like 'field' or 'field[3]' into (key, index)."""
    match = re.match(r"(\w+)(?:\[(\w+)\])?", part)
    if not match:
        raise ValueError(f"Invalid field syntax: {part}")
    key = match.group(1)
    index = match.group(2)
    return key, index


def GetField(obj, field_path: str):
    """Retrieves the value at a nested field path, supporting dot notation and index access."""
    parts = field_path.split('.')
    current = obj

    for i, part in enumerate(parts):
        key, index = parse_part(part)

        # dict or object access
        if isinstance(current, dict):
            if key not in current:
                raise KeyError(f"Key '{key}' not found in dict")
            current = current[key]
        elif hasattr(current, key):
            current = getattr(current, key)
        else:
            raise AttributeError(f"Attribute '{key}' not found")

        # handle indexing or recursive loop
        if isinstance(current, list):
            if index is not None:
                try:
                    current = current[int(index)]
                except (IndexError, ValueError):
                    raise IndexError(f"Invalid index [{index}] for list")
            else:
                # no index provided, collect from all
                rest = '.'.join(parts[i + 1:])
                if not rest:
                    return current
                return [GetField(item, rest) for item in current]

        elif isinstance(current, dict):
            if index is not None:
                if index not in current:
                    raise KeyError(f"Key [{index}] not found in dict")
                current = current[index]
            else:
                # no key provided, collect from all values
                rest = '.'.join(parts[i + 1:])
                if not rest:
                    return current
                return [GetField(value, rest) for value in current.values()]

        else:
            if index is not None:
                raise TypeError(f"Cannot index into non-container at '{key}'")

    return current

def flatten_fields(data, prefix=""):
    fields = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            fields.add(full_key)
            fields |= flatten_fields(value, prefix=full_key)
    return fields


def to_dict(obj):
    return {
        key: value
        for key, value in obj.__dict__.items()
        if not key.startswith('_')
    }
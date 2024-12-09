def is_empty(value):
    return (
        value is None
        or value == ""
        or (isinstance(value, str) and len(value.strip()) == 0)
        or (isinstance(value, dict) and len(value) == 0)
        or (isinstance(value, list) and len(value) == 0)
    )

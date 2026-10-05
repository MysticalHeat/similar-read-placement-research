"""Format embedded notebook settings as readable Python literals."""


def format_literal(value, indentation=0):
    if isinstance(value, dict) and value:
        opening, closing = "{", "}"
        entries = [
            f"{key!r}: {format_literal(item, indentation + 4)}"
            for key, item in value.items()
        ]
    elif isinstance(value, list) and value:
        if len(repr(value)) + indentation <= 80 and not any(isinstance(item, dict) for item in value):
            return repr(value)
        opening, closing = "[", "]"
        entries = [format_literal(item, indentation + 4) for item in value]
    elif type(value) is int:
        return f"{value:_}"
    else:
        return repr(value)

    entry_indent = " " * (indentation + 4)
    closing_indent = " " * indentation
    body = ",\n".join(entry_indent + entry for entry in entries)
    return f"{opening}\n{body},\n{closing_indent}{closing}"

import re

# Format: XX:XX:XXXXXXX:XXXX (digits only, 3 colons)
_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{6,7}:\d{3,4}$")

def is_valid_cadastral(value: str) -> bool:
    if not isinstance(value, str):
        return False
    value = value.strip()
    if value.count(":") != 3:
        return False
    return bool(_PATTERN.match(value))

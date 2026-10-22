import re
from datetime import timedelta

PATTERN = re.compile(r"^(\d+)(s|m|h|d)$", re.I)
MAX_TIMEOUT = timedelta(days=28)


def parse_duration(text):
    match = PATTERN.match(text.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    if amount <= 0:
        return None
    if unit == "s":
        delta = timedelta(seconds=amount)
    elif unit == "m":
        delta = timedelta(minutes=amount)
    elif unit == "h":
        delta = timedelta(hours=amount)
    else:
        delta = timedelta(days=amount)
    if delta > MAX_TIMEOUT:
        return None
    return delta

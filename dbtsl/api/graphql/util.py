import re

pat = re.compile(r"[ \t\n]+")


def normalize_query(s: str) -> str:
    """Return a normalized query string."""
    return pat.subn(" ", s.strip("\n"))[0].strip()

"""Mask account and personal data before text reaches a model, a log or a page.

Keeps just enough for a human to recognise a value (country code, last digits,
email domain). Never touches short identifiers the agents need: person IDs such as
BANK-C or S-2291, items such as 7731 or SE301, request IDs, reason codes and dates.
"""
import re

_EMAIL = re.compile(r"(?<![\w.+-])([A-Za-z0-9])[A-Za-z0-9._%+-]*@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
# Uppercase country code + 2 check digits + 11..30 letters/digits, spaces allowed.
_IBAN = re.compile(r"\b([A-Z]{2}\d{2})((?:[ ]?[A-Z0-9]){11,30})\b")
_CARD = re.compile(r"(?<![\d-])(\d{4})[ -]?(\d{4})[ -]?(\d{4})[ -]?(\d{4})(?![\d-])")
_INTL_PHONE = re.compile(r"(?<![\w+])\+\d{1,3}(?:[ .-]?\(?\d{1,4}\)?){2,5}(?![\w])")
_LOCAL_PHONE = re.compile(r"(?<![\w-])0\d{1,2}[ -]\d{3}[ -]\d{3,4}(?![\w-])")
_LONG_NUMBER = re.compile(r"(?<![\w-])\d{10,18}(?![\w-])")


def _keep_last(digits: str, keep: int = 4) -> str:
    return "*" * (len(digits) - keep) + digits[-keep:]


def _iban(match: re.Match) -> str:
    rest = match.group(2).replace(" ", "")
    if sum(char.isdigit() for char in rest) * 2 < len(rest):
        return match.group(0)  # mostly letters: reason codes such as "BE04 RJCT AC04", not an IBAN
    return f"{match.group(1)} **** **** {rest[-2:]}"


def _phone(match: re.Match) -> str:
    groups = re.findall(r"\+?\d+", match.group(0))
    if sum(len(group.lstrip("+")) for group in groups) < 8:
        return match.group(0)
    if len(groups) == 1:
        number = groups[0]
        return number[0] + _keep_last(number[1:]) if number.startswith("+") else _keep_last(number)
    middle = " ".join("*" * len(group) for group in groups[1:-1])
    first = groups[0] if groups[0].startswith("+") else "*" * len(groups[0])
    return " ".join(part for part in (first, middle, groups[-1]) if part)


def mask(text: str) -> str:
    """Return text with IBANs, cards, account/national IDs, phones and emails masked."""
    if not isinstance(text, str) or not text:
        return text
    text = _EMAIL.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", text)
    text = _IBAN.sub(_iban, text)
    text = _CARD.sub(lambda m: f"**** **** **** {m.group(4)}", text)
    text = _INTL_PHONE.sub(_phone, text)
    text = _LOCAL_PHONE.sub(_phone, text)
    return _LONG_NUMBER.sub(lambda m: _keep_last(m.group(0)), text)


_LEAK_PATTERNS = {
    "email": re.compile(r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "iban": _IBAN,
    "card": _CARD,
    "phone": re.compile(f"{_INTL_PHONE.pattern}|{_LOCAL_PHONE.pattern}"),
    "account_or_national_id": _LONG_NUMBER,
}


def find_leaks(text: str) -> dict[str, int]:
    """Count values that still look unmasked (used by tests and the evaluation)."""
    counts: dict[str, int] = {}
    if not isinstance(text, str):
        return counts
    for name, pattern in _LEAK_PATTERNS.items():
        hits = [m for m in pattern.finditer(text) if mask(m.group(0)) != m.group(0)]
        if hits:
            counts[name] = len(hits)
    return counts

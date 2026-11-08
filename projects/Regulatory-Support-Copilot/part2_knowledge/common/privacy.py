"""Strict Part 2 redaction around the shared Part 5 masking hook.

Patterns cover the project's financial/contact/ID formats, not arbitrary personal
information. They retain short record references, reason codes and ISO dates.
"""
from importlib import import_module
from datetime import date, datetime
import math
import re
import unicodedata

REDACTED = "[REDACTED]"
PRIVACY_VERSION = "strict-v1"
PRIVACY_METADATA_KEY = "privacy_policy"
_PRIVATE_FIELDS = {"iban", "account", "account number", "account no", "acct", "card", "card number",
                   "national id", "national identifier", "phone", "phone number", "telephone", "mobile",
                   "email", "email address", "cvv", "cvc", "ssn", "رقم الحساب", "الرقم الوطني", "هاتف"}

_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ \t]*[A-Z0-9]){11,30}\b", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+*-]+@[\w.-]+\.[^\W\d_]{2,63}\b", re.UNICODE)
_INTERNATIONAL_PHONE = re.compile(r"(?<!\w)(?:\+|00)\d{1,3}(?:[ \t().-]*[\dXx]){7,14}(?!\w)")
_LONG_NUMBER = re.compile(r"(?<!\d)\d(?:[ \t().-]*\d){9,}(?!\d)")
_SSN = re.compile(r"(?<!\d)\d{3}[ -]\d{2}[ -]\d{4}(?!\d)")
_PARTIAL_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ \t]+\*{2,})+[ \t]+\d{1,4}\b", re.IGNORECASE)
_PARTIAL_PHONE = re.compile(r"(?<!\w)\+?\d{1,3}(?:[ \t-]+\*{2,})+[ \t-]+\d{1,4}(?!\w)")
_PARTIAL_NUMBER = re.compile(r"(?<!\w)\*{3,}(?:[ \t]+\*{3,})*[ \t]*\d{1,4}(?!\w)")
_ISO_DATE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
                       r"(?:Z|[+-]\d{2}:\d{2})?)?(?!\d)")
_LABELLED_NUMBER = re.compile(
    r"(?i)\b(?:account(?:\s*(?:number|no\.?))?|acct|card(?:\s*(?:number|no\.?))?|"
    r"national\s*(?:id|identifier)|phone|mobile|tel(?:ephone)?|cvv|cvc|ssn|"
    r"رقم[ \t]+(?:الحساب|البطاقة|الهاتف)|الرقم[ \t]+الوطني|هاتف|جوال|موبايل)"
    r"[ \t]*(?:[:=#][ \t]*)?(\+?\d(?:[ \t().-]*[\dXx]){2,18})(?!\w)"
)


class PrivacyError(RuntimeError):
    """Privacy filtering could not complete; no unfiltered data may continue."""


def _private_field(name: str) -> bool:
    return re.sub(r"[\W_]+", " ", name).strip().casefold() in _PRIVATE_FIELDS


def _redact(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(str(unicodedata.decimal(char)) if char.isdecimal() else char
                   for char in text if unicodedata.category(char) != "Cf")
    for pattern in (_PARTIAL_IBAN, _PARTIAL_PHONE, _PARTIAL_NUMBER):
        text = pattern.sub(REDACTED, text)
    # Numeric content distinguishes IBAN-shaped values from short reason codes
    # followed by ordinary prose. Invalid fictional IBANs are redacted as well.
    text = _IBAN.sub(lambda match: REDACTED if sum(c.isdigit() for c in match[0]) >= 6 else match[0], text)
    text = _EMAIL.sub(REDACTED, text)
    text = _SSN.sub(REDACTED, text)
    text = _INTERNATIONAL_PHONE.sub(REDACTED, text)
    text = _LABELLED_NUMBER.sub(lambda match: match[0][:match.start(1) - match.start()] + REDACTED, text)
    dates = {}
    def keep_date(match):
        value = match[0]
        try:
            if "T" in value or " " in value:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                date.fromisoformat(value)
        except ValueError:
            return value
        suffix = str(len(dates)).translate(str.maketrans("0123456789", "ABCDEFGHIJ"))
        token = f"\ufff0DATE{suffix}\ufff1"
        dates[token] = value
        return token
    text = _LONG_NUMBER.sub(REDACTED, _ISO_DATE.sub(keep_date, text))
    for token, value in dates.items():
        text = text.replace(token, value)
    return text


def mask_text(text: str) -> str:
    """Fully redact detected values, use Part 5 when present, and recheck output."""
    if not isinstance(text, str):
        raise PrivacyError("Privacy filtering requires text.")
    safe = _redact(text)
    try:
        module = import_module("part5_web.safety.masking")
    except ModuleNotFoundError as exc:
        if exc.name in {"part5_web", "part5_web.safety", "part5_web.safety.masking"}:
            return safe
        raise PrivacyError("Part 5 masking has a missing dependency; processing stopped.") from None
    except Exception:
        raise PrivacyError("Part 5 masking could not load; processing stopped.") from None
    try:
        masked = module.mask(safe)
        if not isinstance(masked, str):
            raise TypeError
        return _redact(masked)
    except Exception:
        raise PrivacyError("Part 5 masking failed; processing stopped.") from None


def sanitize(value):
    """Return a redacted copy of JSON-compatible data, including metadata keys."""
    if isinstance(value, str):
        return mask_text(value)
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise PrivacyError("Non-finite data cannot be privacy-filtered.")
        if (isinstance(value, int) or value.is_integer()) and len(str(abs(int(value)))) >= 10:
            return REDACTED
        return value
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        safe = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise PrivacyError("Privacy-filtered object keys must be strings.")
            # Keys are structural; strict local redaction keeps a hook from rewriting
            # normal JSON-schema field names while still hiding private key values.
            safe_key = _redact(key)
            if safe_key in safe:
                raise PrivacyError("Redacted object keys collide; processing stopped.")
            safe[safe_key] = REDACTED if _private_field(key) and item is not None else sanitize(item)
        return safe
    raise PrivacyError("Unsupported data type at the privacy boundary.")


def sanitize_schema(schema: dict) -> dict:
    """Preserve JSON-schema structure while filtering examples and private defaults."""
    def visit(node, private=False):
        if isinstance(node, dict):
            result = {}
            for key, value in node.items():
                safe_key = _redact(key)
                if safe_key in result:
                    raise PrivacyError("Redacted schema keys collide; processing stopped.")
                if key == "properties":
                    properties = {}
                    for name, definition in value.items():
                        safe_name = _redact(name)
                        if safe_name in properties:
                            raise PrivacyError("Redacted property names collide; processing stopped.")
                        properties[safe_name] = visit(definition, _private_field(name))
                    result[safe_key] = properties
                elif key in {"example", "examples", "default", "const", "enum"}:
                    if private and value is not None:
                        result[safe_key] = [REDACTED for _ in value] if key in {"examples", "enum"} else REDACTED
                    else:
                        result[safe_key] = sanitize(value)
                else:
                    result[safe_key] = visit(value)
            return result
        if isinstance(node, list):
            return [visit(item, private) for item in node]
        if isinstance(node, str):
            return mask_text(node)
        if node is None or isinstance(node, (int, float, bool)):
            return node
        raise PrivacyError("Unsupported value in a provider schema.")
    return visit(schema)

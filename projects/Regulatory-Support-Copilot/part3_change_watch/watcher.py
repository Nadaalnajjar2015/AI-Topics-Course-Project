"""Change Watcher: extract with the shared LLM, verify quotes with code."""
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
import logging
import re

from contracts.schemas import ChangeDocument, ChangeSummary, Requirement
from part1_templates.tools.templates import load_template
from part2_knowledge.common import llm
from part3_change_watch._support import Extraction, data_tag, prompt

logger = logging.getLogger(__name__)


def normalize(text):
    return " ".join(text.split())


@dataclass(frozen=True)
class Section:
    number: str
    line: int
    text: str


def sections(text: str) -> list[Section]:
    """Preserve original numbered spans; exclude front matter and background."""
    lines = text.splitlines(keepends=True)
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            raise ValueError("Unclosed change document front matter.")
        start = end + 1
    result, pending, number, first = [], [], None, 0
    excluded = False
    for i in range(start, len(lines)):
        line = lines[i]
        heading = re.match(r"^\s*#{1,6}\s+(.+)", line)
        match = re.match(r"^\s*(?:#{1,6}\s+)?(\d+(?:\.\d+)*)(?:[.)](?=\s)|(?=\s))\s+", line)
        if match or heading:
            if number is not None:
                result.append(Section(number, first, "".join(pending).rstrip()))
            pending, number = [], None
        if heading and not match:
            excluded = bool(re.search(r"background|context|history|introduction", heading[1], re.I))
            continue
        if match and not excluded:
            number, first = match[1], i + 1
            pending = [line[match.end():]]
        elif number is not None:
            pending.append(line)
    if number is not None:
        result.append(Section(number, first, "".join(pending).rstrip()))
    return result


def verbatim(quote, text):
    words = quote.split()
    if not words:
        return None
    match = re.search(r"\s+".join(re.escape(w) for w in words), text)
    return match.group() if match else None


def verified_quote(quote, section):
    exact = verbatim(quote, section.text)
    if exact:
        return exact
    # Only punctuation/case differences may be repaired. Identical word/number
    # tokens prevent near-matches from changing negation, limits, dates or codes.
    tokens = lambda value: re.findall(r"\w+", value.casefold())
    for sentence in re.split(r"(?<=[.!?])\s+", section.text):
        if (tokens(quote) == tokens(sentence)
                and SequenceMatcher(None, normalize(quote).casefold(), normalize(sentence).casefold()).ratio() >= .92):
            return sentence
    return None


def _verified_date(extraction, doc):
    if doc.effective is not None:
        return doc.effective
    if not extraction.effective_date or not extraction.effective_quote:
        return None
    if not verbatim(extraction.effective_quote, doc.text):
        return None
    try:
        parsed = date.fromisoformat(extraction.effective_date)
    except ValueError:
        return None
    # Require the date in the quoted effective clause, not just publication metadata.
    forms = {parsed.isoformat(), f"{parsed.day} {parsed.strftime('%B')} {parsed.year}",
             f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"}
    quote = normalize(extraction.effective_quote)
    if (any(form in quote for form in forms)
            and re.search(r"effective|from|commenc|takes effect", quote, re.I)):
        return parsed
    return None


def summarize(doc: ChangeDocument) -> ChangeSummary:
    """Return independently verified requirements; never persist or approve."""
    template = load_template(doc.template_id)
    if not doc.text.strip():
        raise ValueError("Change document text must not be empty.")
    chunks = sections(doc.text)
    extraction = llm.complete_json(prompt("watcher", template), data_tag("document", {
        "text": doc.text, "sections": [vars(section) for section in chunks],
    }), Extraction)
    accepted, seen = [], set()
    for candidate in extraction.requirements:
        matching = [s for s in chunks if candidate.source_location in {
            s.number, f"Section {s.number}", f"Section {s.number}, line {s.line}"}]
        if len(matching) != 1:
            logger.warning("Dropped requirement with unverifiable section.")
            continue
        section = matching[0]
        quote = verified_quote(candidate.source_quote, section)
        if not quote or not verbatim(quote, doc.text):
            logger.warning("Dropped requirement with unverifiable source quote.")
            continue
        key = (normalize(quote), normalize(candidate.description).casefold())
        if key not in seen:
            seen.add(key)
            accepted.append((section.line, section.text.find(quote), candidate, quote))
    requirements = []
    for _, _, candidate, quote in sorted(accepted, key=lambda item: (item[0], item[1], item[2].description)):
        section = next(s for s in chunks if candidate.source_location in {
            s.number, f"Section {s.number}", f"Section {s.number}, line {s.line}"})
        requirements.append(Requirement(
            requirement_id=f"{doc.change_id}-R{len(requirements) + 1}", description=candidate.description,
            category=candidate.category, mandatory=candidate.mandatory, source_quote=quote,
            source_location=f"Section {section.number}, line {section.line}",
        ))
    return ChangeSummary(change_id=doc.change_id, template_id=doc.template_id, title=doc.title,
                         scope=doc.scope, effective_date=_verified_date(extraction, doc),
                         summary_text=extraction.summary_text, requirements=requirements)

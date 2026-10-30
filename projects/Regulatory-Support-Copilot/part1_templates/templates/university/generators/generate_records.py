"""MOCK DATA – fictional, for a student prototype.

Seed 42; planted requests retain these exact outcomes. Background records for a
planted person use other courses so the latest evidence stays unambiguous.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import random

NOTE = "MOCK DATA – fictional, for a student prototype"
PLANTED = [
    ("R-48207", "S-2290", "CS-BSc", "CS330", "WAITLISTED", "SECTION_FULL", "Section full; join the waiting list"),
    ("R-48208", "S-2301", "BUS-BBA", "BUS210", "BLOCKED", "FEES_UNPAID", "Unpaid fees have placed a registration hold"),
    ("R-48209", "S-2315", "SE-BSc", "SE220", "BLOCKED", "TIME_CONFLICT", "Timetable overlaps an existing section"),
    ("R-48210", "S-2320", "CS-BSc", "CS340", "BLOCKED", "CREDIT_LIMIT", "Sixth course would exceed the 18-credit limit"),
    ("R-48211", "S-2333", "NUR-BSc", "NUR210", "BLOCKED", "ADVISOR_HOLD", "Academic advisor approval is outstanding"),
    ("R-48212", "S-2288", "BUS-BBA", "BUS101", "REGISTERED", None, "Registration completed successfully"),
    ("R-48213", "S-2291", "SE-BSc", "SE301", "BLOCKED", "PREREQ_MISSING", "Missing prerequisite SE201; fictional ID 0000002291, phone +962 7X XXX XXXX"),
    ("R-48214", "S-2360", "SE-BSc", "SE310", "BLOCKED", "PREREQ_MISSING", "Missing prerequisite SE220"),
    ("R-48215", "S-2412", "CS-BSc", "CS101", "REGISTERED", None, "Registration completed successfully"),
]
REASONS = {
    "PREREQ_MISSING": "Required prerequisite has not been passed",
    "SECTION_FULL": "Section has reached its capacity", "FEES_UNPAID": "Unpaid fees hold",
    "TIME_CONFLICT": "Timetable conflict", "CREDIT_LIMIT": "Credit limit exceeded",
    "ADVISOR_HOLD": "Advisor approval required", "LATE_REGISTRATION": "Registration deadline passed",
}
COURSES = {"CS-BSc": ["CS101", "CS330", "CS340"], "SE-BSc": ["SE201", "SE220", "SE301", "SE310"],
           "BUS-BBA": ["BUS101", "BUS210"], "NUR-BSc": ["NUR101", "NUR210"]}
PREREQUISITES = {"CS330": "CS201", "CS340": "CS201", "SE201": "SE101", "SE220": "SE201",
                 "SE301": "SE201", "SE310": "SE220", "BUS210": "BUS101", "NUR210": "NUR101"}


def generate(output_path=None) -> Path:
    """Write exactly 250 registrations for 50 fictional students."""
    random.seed(42)
    root = Path(__file__).resolve().parents[1]
    rows = []
    for index, (identifier, person, unit, item, status, reason, detail) in enumerate(PLANTED):
        stamp = datetime(2026, 2, 10, 9, 19) + timedelta(minutes=index - 6)
        rows.append(dict(record_id=identifier, template_id="university", timestamp=stamp.isoformat(),
                         person_id=person, unit_id=unit, item=item, status=status, reason_code=reason, detail=detail))
    # Nine named students and 41 background students; S-2399 intentionally has no records.
    population = [(person, unit) for _, person, unit, *_ in PLANTED]
    population.extend((f"S-{2500 + index}", list(COURSES)[index % 4]) for index in range(41))
    reserved = {(row["person_id"], row["item"]) for row in rows}
    for index in range(250 - len(rows)):
        person, unit = population[index % len(population)]
        item = random.choice([course for course in COURSES[unit] if (person, course) not in reserved])
        reason = random.choice(list(REASONS)) if index % 5 == 0 else None
        if reason == "PREREQ_MISSING" and item not in PREREQUISITES:
            reason = "ADVISOR_HOLD"
        stamp = datetime(2026, 2, 8) + timedelta(seconds=random.randrange(5 * 86400))
        if reason == "LATE_REGISTRATION":
            stamp = datetime(2026, 2, 12, 18, 0) + timedelta(minutes=index)
        detail = REASONS[reason] if reason else "Registration completed successfully"
        if reason == "PREREQ_MISSING":
            detail = f"Missing prerequisite {PREREQUISITES[item]}"
        rows.append(dict(record_id=f"R-{50000 + index}", template_id="university", timestamp=stamp.isoformat(),
                         person_id=person, unit_id=unit, item=item,
                         status=("WAITLISTED" if reason == "SECTION_FULL" else "BLOCKED") if reason else "REGISTERED",
                         reason_code=reason, detail=detail))
    output = Path(output_path) if output_path is not None else root / "records" / "registrations.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in [{"_note": NOTE}, *rows]:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output


if __name__ == "__main__":
    print(generate())

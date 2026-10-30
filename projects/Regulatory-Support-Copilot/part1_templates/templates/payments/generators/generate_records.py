"""MOCK DATA – fictional, for a student prototype.

Regenerate transactions.jsonl with seed 42. Planted records are listed here;
random references use a disjoint range so they cannot overwrite ticket evidence.
"""
import json
from pathlib import Path
import random
from datetime import datetime, timedelta

NOTE = "MOCK DATA – fictional, for a student prototype"
PLANTED = [
    ("T-100451", "BANK-A", "ACH", "8820", "RETURNED", "AC01", "Incorrect creditor account number"),
    ("T-100452", "BANK-B", "ACH", "7745", "REJECTED", "AM04", "Insufficient funds in debtor account"),
    ("T-100453", "BANK-B", "IPS", "8012", "REJECTED", "BE04", "Missing structured creditor address: PstlAdr/TwnNm and Ctry"),
    ("T-100454", "BANK-D", "ACH", "9102", "REJECTED", "RC01", "Incorrect creditor bank identifier"),
    ("T-100455", "BANK-E", "WAL", "6650", "REJECTED", "AG01", "Transaction forbidden for the basic KYC wallet tier"),
    ("T-100456", "BANK-A", "ACH", "8125", "REJECTED", "FF01", "Invalid pacs.008 file format"),
    ("T-100457", "BANK-C", "ACH", "7731", "REJECTED", "AC04", "pacs.002 RJCT: creditor account closed (fictional acct 0013100030212)"),
    ("T-100458", "BANK-C", "CHQ", "7790", "RETURNED", "TM01", "Cut-off time passed: cheque presented after 15:00"),
    ("T-100459", "BANK-D", "IPS", "9150", "REJECTED", "AM05", "Duplicate payment: EndToEndId already processed"),
    ("T-100460", "BANK-B", "ACH", "7802", "REJECTED", "AC06", "Creditor account blocked"),
    ("T-100461", "BANK-A", "IPS", "8301", "SETTLED", None, "pacs.002 accepted and settled successfully"),
    ("T-100462", "BANK-E", "IPS", "6688", "REJECTED", "RR01", "Missing debtor identification in Dbtr/Id"),
    ("T-100463", "BANK-D", "RPT", "9200", "REJECTED", "MS03", "Reason not specified by reporting gateway; manual investigation required"),
]
REASONS = {
    "AC01": "Incorrect account number", "AC04": "Closed creditor account",
    "AC06": "Blocked account", "AG01": "Transaction forbidden",
    "AM04": "Insufficient funds", "AM05": "Duplicate payment",
    "BE04": "Missing creditor address", "FF01": "Invalid file format",
    "RC01": "Incorrect bank identifier", "RR01": "Missing debtor identification",
    "MS03": "Reason not specified", "TM01": "Cut-off time passed",
}
MODULE_REASONS = {
    "CHQ": ["AC01", "AC04", "AC06", "AM04", "FF01", "TM01"],
    "ACH": list(REASONS),
    "IPS": [code for code in REASONS if code != "TM01"],
    "WAL": ["AC01", "AC04", "AC06", "AG01", "AM04", "AM05", "BE04", "FF01", "RC01", "RR01", "MS03"],
    "RPT": ["FF01", "MS03", "TM01"],
}


def generate(output_path=None) -> Path:
    """Write exactly 500 deterministic records, including 75 failed outcomes."""
    random.seed(42)
    root = Path(__file__).resolve().parents[1]
    stakeholders = json.loads((root / "stakeholders.json").read_text(encoding="utf-8"))["stakeholders"]
    rows = []
    for index, (identifier, person, unit, item, status, reason, detail) in enumerate(PLANTED):
        stamp = datetime(2026, 3, 2, 9, 12, 3) + timedelta(minutes=index - 6)
        if item == "7790":
            stamp = datetime(2026, 3, 2, 15, 5)
        rows.append(dict(record_id=identifier, template_id="payments", timestamp=stamp.isoformat(),
                         person_id=person, unit_id=unit, item=item, status=status, reason_code=reason, detail=detail))
    failures = 75 - sum(row["reason_code"] is not None for row in rows)
    failed_indices = set(random.sample(range(500 - len(rows)), failures))
    for index in range(500 - len(rows)):
        group = random.choice(stakeholders)
        unit = random.choice(group["units"])
        reason = random.choice(MODULE_REASONS[unit]) if index in failed_indices else None
        detail = REASONS[reason] if reason else "Accepted and settled successfully"
        if index % 37 == 0:
            detail += "; fictional IBAN JO00 MOCK 0000 0000 0000 0000 00; fictional acct 0013100030212"
        stamp = datetime(2026, 3, 1) + timedelta(seconds=random.randrange(3 * 86400))
        if reason == "TM01":
            stamp = stamp.replace(hour=16)
        rows.append(dict(record_id=f"T-{200000 + index}", template_id="payments", timestamp=stamp.isoformat(),
                         person_id=group["stakeholder_id"], unit_id=unit, item=str(20000 + index),
                         status=random.choice(["REJECTED", "RETURNED"]) if reason else "SETTLED",
                         reason_code=reason, detail=detail))
    output = Path(output_path) if output_path is not None else root / "records" / "transactions.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in [{"_note": NOTE}, *rows]:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output


if __name__ == "__main__":
    print(generate())

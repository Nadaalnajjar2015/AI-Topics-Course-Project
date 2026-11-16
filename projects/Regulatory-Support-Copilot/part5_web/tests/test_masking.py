import pytest

from part2_knowledge.common import llm
from part5_web.safety import masking
from part5_web.safety.masking import find_leaks, mask


@pytest.mark.parametrize(("text", "expected"), [
    # Guide examples, payments template
    ("JO71 CBJO 0010 0000 0000 0131 0003 02", "JO71 **** **** 02"),
    ("JO71CBJO0010000000000131000302", "JO71 **** **** 02"),
    ("fictional acct 0013100030212", "fictional acct *********0212"),
    ("card 4111 1111 1111 1111", "card **** **** **** 1111"),
    ("card 4111-1111-1111-1111", "card **** **** **** 1111"),
    ("card 4111111111111111", "card **** **** **** 1111"),
    ("ops@northfield-bank.example", "o***@northfield-bank.example"),
    # University template
    ("national ID 9881023456", "national ID ******3456"),
    ("call +962 79 123 4567 today", "call +962 ** *** 4567 today"),
    ("call 079 123 4567", "call *** *** 4567"),
    ("s.haddad@northfield.example", "s***@northfield.example"),
])
def test_masks_each_kind(text, expected):
    assert mask(text) == expected


@pytest.mark.parametrize("text", [
    "BANK-C asks why payment 7731 was rejected with AC04.",
    "S-2291 cannot register for SE301: PREREQ_MISSING (needs SE201).",
    "Request P-REQ-007 and U-REQ-007 on 2026-03-02T09:12:03, record T-100457.",
    "CHG-P-002 effective 2026-06-01; reason codes BE04 RJCT AC04 FF01 RR01.",
    "",
])
def test_keeps_identifiers_agents_need(text):
    assert mask(text) == text


def test_several_values_in_one_text():
    text = ("BANK-C (ops@eastgate.example, +962 79 123 4567) sent 7731 from JO71 CBJO 0010 0000 0000 0131 0003 02 "
            "and account 0013100030212.")
    masked = mask(text)
    assert "BANK-C" in masked and "7731" in masked
    assert "o***@eastgate.example" in masked and "+962 ** *** 4567" in masked
    assert "JO71 **** **** 02" in masked and "*********0212" in masked
    assert find_leaks(masked) == {}


def test_mask_is_idempotent_and_handles_non_text():
    once = mask("JO71 CBJO 0010 0000 0000 0131 0003 02, 9881023456, a.b@x.example")
    assert mask(once) == once
    assert mask(None) is None


def test_find_leaks_counts_unmasked_values():
    assert find_leaks("acct 0013100030212 and s.haddad@northfield.example") == {
        "email": 1, "account_or_national_id": 1}
    assert find_leaks("record T-100457, payment 7731") == {}


def test_llm_receives_masked_text(monkeypatch):
    """End to end: Part 2's llm.py calls this mask() before the provider sees the prompt."""
    seen, calls = {}, []
    real_mask = masking.mask
    monkeypatch.setattr(masking, "mask", lambda text: calls.append(text) or real_mask(text))
    monkeypatch.setattr(llm, "_fake_text", lambda system, user: seen.update(system=system, user=user) or "ok")
    llm.complete_text("You are a support agent.",
                      "IBAN JO71 CBJO 0010 0000 0000 0131 0003 02, acct 0013100030212, national ID 9881023456, "
                      "phone +962 79 123 4567, email ops@northfield-bank.example, payment 7731 from BANK-C")
    assert calls, "Part 2 did not call part5_web.safety.masking.mask"
    sent = seen["system"] + seen["user"]
    for secret in ("CBJO 0010", "0013100030212", "9881023456", "79 123 4567", "ops@northfield"):
        assert secret not in sent
    assert "7731" in sent and "BANK-C" in sent

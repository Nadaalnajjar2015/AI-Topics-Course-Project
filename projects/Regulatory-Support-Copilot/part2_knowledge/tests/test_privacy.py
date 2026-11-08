"""Fictional fixtures only: inspect provider, embedding, storage and output boundaries."""
from copy import deepcopy
import json
import traceback
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, model_validator

from contracts import schemas
from part2_knowledge.common import llm, privacy
from part2_knowledge.knowledge_base import _store, ingest
from part2_knowledge.knowledge_base.chunking import Chunk, chunk_markdown
from part2_knowledge.knowledge_base.search import search
from part2_knowledge.tests.conftest import TinyEmbedding

ACCOUNT = "0013100030212"
PHONE = "+962 79 123 4567"
IBAN = "JO71 CBJO 0010 0000 0000 0131 0003 02"
CARD = "4111 1111 1111 1111"
NATIONAL_ID = "9881023456"
EMAIL = "ops@fictional-bank.example"
PRIVATE_TEXT = f"IBAN {IBAN}; phone {PHONE}; account {ACCOUNT}; card {CARD}; national ID {NATIONAL_ID}; email {EMAIL}."


@pytest.fixture(autouse=True)
def absent_part5(monkeypatch):
    def missing(name):
        raise ModuleNotFoundError(name, name=name)
    monkeypatch.setattr(privacy, "import_module", missing)


@pytest.mark.parametrize("value", [
    IBAN, IBAN.replace(" ", ""), "GB82 WEST 1234 5698 7654 32", "DE89370400440532013000",
    "FR1420041010050500013M02606", "JO00 MOCK 0000 0000 0000 0000 00", PHONE,
    "+1 (202) 555-0123", "0771234567", "+962 7X XXX XXXX", ACCOUNT, CARD,
    "4111-1111-1111-1111", "378282246310005", NATIONAL_ID, "123-45-6789", EMAIL,
    "٩٨٨١٠٢٣٤٥٦", "９８８１０２３４５６", "98810\u200b23456",
    "JO71 **** **** 02", "+962 ** *** 4567", "*********0212", "**** **** **** 1111",
    "******3456", "o***@fictional-bank.example", "123456789012345678901234567890",
])
def test_private_formats_are_fully_hidden(value):
    assert privacy.mask_text(value) == privacy.REDACTED


@pytest.mark.parametrize("text,value", [
    ("account: 12345678", "12345678"), ("national ID: 1234567", "1234567"),
    ("phone 5551234", "5551234"), ("رقم الحساب: 12345678", "12345678"),
    ("هاتف: 5551234", "5551234"), ("CVV: 123", "123"),
    ("national ID: 2026-09-01", "2026-09-01"),
])
def test_labels_cover_shorter_private_numbers(text, value):
    result = privacy.mask_text(text)
    assert value not in result and privacy.REDACTED in result


@pytest.mark.parametrize("text", [
    "BANK-C S-2291 payment 7731 SE301 AC04 PREREQ_MISSING CHG-P-002 ACH-R07",
    "2026-09-01 17:00 18 credits 15% 10% 100000",
    "2026-09-01T17:00:00+03:00",
    "pacs.008.001.08 pacs.008.001.10 camt.053",
    "**Policy** applies in 2026; unit SE-BSc.",
])
def test_nonprivate_identifiers_dates_and_rules_remain_usable(text):
    assert privacy.mask_text(text) == text


def test_redaction_is_idempotent_and_nested_payloads_are_copied():
    original = {"metadata": {"owner": EMAIL, "national_id": 9881023456},
                "items": [PRIVATE_TEXT, True, None, 18], "date": "2026-09-01"}
    snapshot = deepcopy(original)
    safe = privacy.sanitize(original)
    assert original == snapshot
    assert safe["metadata"] == {"owner": privacy.REDACTED, "national_id": privacy.REDACTED}
    assert safe["items"][1:] == [True, None, 18]
    assert safe["date"] == "2026-09-01"
    assert privacy.sanitize(safe) == safe
    assert all(value not in json.dumps(safe) for value in (ACCOUNT, PHONE, IBAN, CARD, NATIONAL_ID, EMAIL))


def test_named_private_fields_hide_short_or_date_shaped_values():
    safe = privacy.sanitize({"account_number": "1234", "national_id": "2026-09-01",
                             "phone": "5551234", "record_id": "T-100457"})
    assert safe == {"account_number": privacy.REDACTED, "national_id": privacy.REDACTED,
                    "phone": privacy.REDACTED, "record_id": "T-100457"}


def test_schema_defaults_and_validated_defaults_are_redacted(monkeypatch):
    class WithDefault(BaseModel):
        national_id: str = "12345678"
        model_config = {"json_schema_extra": {"example": {}}}
    seen = []
    def provider(system, user, schema):
        seen.append(schema)
        return deepcopy(schema["example"])
    monkeypatch.setattr(llm, "_fake_json", provider)
    result = llm.complete_json("System", "User", WithDefault)
    assert result.national_id == privacy.REDACTED
    assert seen[0]["properties"]["national_id"]["default"] == privacy.REDACTED
    assert "12345678" not in json.dumps(seen)


def test_validator_cannot_reintroduce_private_data():
    class UnsafeValidator(BaseModel):
        value: str
        model_config = {"json_schema_extra": {"example": {"value": "safe"}}}

        @model_validator(mode="after")
        def inject_private_value(self):
            self.value = ACCOUNT
            return self

    with pytest.raises(privacy.PrivacyError, match="reintroduced private data"):
        llm.complete_json("System", "User", UnsafeValidator)


def test_part5_is_called_with_already_redacted_text_and_output_is_rechecked(monkeypatch):
    seen = []
    def hook(text):
        seen.append(text)
        return text + " " + PHONE
    monkeypatch.setattr(privacy, "import_module", lambda name: SimpleNamespace(mask=hook))
    safe = privacy.mask_text(PRIVATE_TEXT)
    assert seen and ACCOUNT not in seen[0] and PHONE not in seen[0]
    assert PHONE not in safe and IBAN not in safe


@pytest.mark.parametrize("failure", ["raise", "nontext", "import"])
def test_masking_failure_stops_provider_and_hides_error_context(monkeypatch, failure, caplog):
    called = []
    def broken(text):
        if failure == "raise":
            raise ValueError(PRIVATE_TEXT)
        return None
    def load(name):
        if failure == "import":
            raise RuntimeError(PRIVATE_TEXT)
        return SimpleNamespace(mask=broken)
    monkeypatch.setattr(privacy, "import_module", load)
    monkeypatch.setattr(llm, "_fake_text", lambda *args: called.append(args))
    with pytest.raises(privacy.PrivacyError) as error:
        llm.complete_text(PRIVATE_TEXT, PRIVATE_TEXT)
    assert not called
    rendered = "".join(traceback.format_exception(error.type, error.value, error.tb)) + caplog.text
    assert ACCOUNT not in rendered and PHONE not in rendered


def test_unsupported_data_and_colliding_private_keys_fail_closed():
    with pytest.raises(privacy.PrivacyError, match="collide"):
        privacy.sanitize({EMAIL: "one", "other@fictional-bank.example": "two"})
    with pytest.raises(privacy.PrivacyError, match="Unsupported"):
        privacy.sanitize(object())


def test_provider_gets_redacted_prompts_and_schema_examples(monkeypatch):
    seen = []
    original = deepcopy(schemas.Record.model_config["json_schema_extra"]["example"])
    def provider(system, user, schema):
        seen.append({"system": system, "user": user, "schema": schema})
        return deepcopy(schema["example"])
    monkeypatch.setattr(llm, "_fake_json", provider)
    result = llm.complete_json(PRIVATE_TEXT, PRIVATE_TEXT, schemas.Record)
    encoded = json.dumps(seen)
    assert all(value not in encoded for value in (ACCOUNT, PHONE, IBAN, CARD, NATIONAL_ID, EMAIL))
    assert ACCOUNT not in result.detail and privacy.REDACTED in result.detail
    assert schemas.Record.model_config["json_schema_extra"]["example"] == original


def test_provider_output_is_redacted_before_return(monkeypatch):
    monkeypatch.setattr(llm, "_fake_text", lambda *args: PRIVATE_TEXT)
    result = llm.complete_text("System", "User")
    assert all(value not in result for value in (ACCOUNT, PHONE, IBAN, CARD, NATIONAL_ID, EMAIL))


def test_private_values_cannot_leak_across_chunk_boundaries():
    chunks = chunk_markdown("# Guide\n## Contact\n" + "x" * 790 + " " + ACCOUNT + " tail",
                            "guide.md", "payments")
    text = " ".join(chunk.text for chunk in chunks)
    assert ACCOUNT not in text and ACCOUNT[:6] not in text and ACCOUNT[-6:] not in text
    assert privacy.REDACTED in text


class RecordingEmbedding(TinyEmbedding):
    def __init__(self):
        self.calls = []

    def __call__(self, input):
        self.calls.extend(input)
        return super().__call__(input)


def test_embedding_storage_query_and_retrieval_are_redacted(tiny_store, monkeypatch):
    embedding = RecordingEmbedding()
    monkeypatch.setattr(_store, "_embedding_function", lambda: embedding)
    metadata = {"source": f"fixtures/{ACCOUNT}.md", "doc_type": "document", "location": EMAIL,
                "template_id": "payments", "phone": PHONE, "national_id": 9881023456}
    chunks = [Chunk(f"fixtures/{ACCOUNT}.md#0", PRIVATE_TEXT, metadata)]
    monkeypatch.setattr(ingest, "_load_chunks", lambda template_id: (chunks, 1))
    ingest.ingest_all("payments")
    collection = tiny_store.get_collection("kb_payments", embedding_function=embedding)
    stored = collection.get(include=["documents", "metadatas"])
    assert collection.metadata[privacy.PRIVACY_METADATA_KEY] == privacy.PRIVACY_VERSION
    assert stored["ids"][0].startswith("private-source#")
    encoded = json.dumps(stored) + json.dumps(embedding.calls)
    assert all(value not in encoded for value in (ACCOUNT, PHONE, IBAN, CARD, NATIONAL_ID, EMAIL))

    # Simulate corrupt/externally written data without passing it through an embedder.
    collection.update(ids=stored["ids"], documents=[PRIVATE_TEXT], metadatas=[metadata],
                      embeddings=[[1.0, 0.0, 0.0]])
    results = search(PRIVATE_TEXT, filters={"phone": PHONE}, template_id="payments")
    # The filter was redacted, so it cannot use a raw private lookup key.
    assert results == []
    results = search(PRIVATE_TEXT, template_id="payments")
    assert results
    encoded = json.dumps([row.model_dump() for row in results]) + json.dumps(embedding.calls)
    assert all(value not in encoded for value in (ACCOUNT, PHONE, IBAN, CARD, NATIONAL_ID, EMAIL))


def test_legacy_indexes_are_rejected_before_query_embedding(tiny_store, monkeypatch):
    embedding = RecordingEmbedding()
    monkeypatch.setattr(_store, "_embedding_function", lambda: embedding)
    collection = tiny_store.create_collection("kb_payments", embedding_function=embedding,
                                              configuration={"hnsw": {"space": "cosine"}})
    collection.add(ids=["legacy"], documents=[PRIVATE_TEXT],
                   metadatas=[{"template_id": "payments"}], embeddings=[[1.0, 0.0, 0.0]])
    with pytest.raises(privacy.PrivacyError, match="older privacy policy"):
        search("AC04", template_id="payments")
    assert not embedding.calls

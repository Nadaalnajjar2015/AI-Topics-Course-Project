"""Opt-in two-call non-sensitive smoke test; never imported by pytest."""
import argparse
import json
import time

from pydantic import BaseModel, Field

from part2_knowledge.common import llm
from part2_knowledge.common.config import settings


class SmokeAnswer(BaseModel):
    result: str = Field(description="The uppercase form of the supplied word.")


def smoke():
    if settings.llm_provider != "groq" or not settings.groq_api_key.strip():
        raise llm.LLMError("LIVE GROQ TEST NOT RUN: select groq and configure a local key.")
    text = llm.complete_text("Answer briefly.", "Say hello.")
    time.sleep(3)
    answer = llm.complete_json("Return the uppercase form as JSON.", "hello", SmokeAnswer)
    if not text.strip() or answer.result != "HELLO":
        raise llm.LLMError("Live smoke output did not satisfy the non-sensitive task.")
    return {"live_smoke": "passed", "model": settings.llm_model, "calls": 2,
                      "response_mode": "json_schema/strict=false" if settings.llm_model in {
                          "openai/gpt-oss-20b", "openai/gpt-oss-120b", "openai/gpt-oss-safeguard-20b",
                          "qwen/qwen3.8-27b", "meta-models/muse-spark-open"}
                      else "json_object"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true", required=True)
    parser.parse_args(argv)
    try:
        print(json.dumps(smoke()))
        return 0
    except llm.LLMError as exc:
        print(str(exc))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

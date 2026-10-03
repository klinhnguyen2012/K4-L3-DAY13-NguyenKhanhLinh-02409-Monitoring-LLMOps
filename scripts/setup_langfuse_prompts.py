from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client
from langfuse.api.prompts.types.create_text_prompt_request import CreateTextPromptRequest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.prompt_management import DEFAULT_PROMPT_TEMPLATE


PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
BASELINE_TEMPLATE = DEFAULT_PROMPT_TEMPLATE
CANDIDATE_TEMPLATE = (
    "Feature={{feature}}\n\n"
    "Use only relevant evidence from the context. If the context does not support an answer, "
    "state what is missing instead of guessing.\n\n"
    "Context:\n{{docs}}\n\nCustomer question:\n{{message}}"
)


def main() -> int:
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("Thiếu LANGFUSE_PUBLIC_KEY hoặc LANGFUSE_SECRET_KEY trong .env.")
        return 1

    client = get_client()
    prompts = client.api.prompts.list(name=PROMPT_NAME, limit=20).data
    if prompts:
        print(f"Prompt {PROMPT_NAME!r} đã tồn tại; không tạo version trùng.")
        for prompt in prompts:
            print(f"versions={prompt.versions}; labels={prompt.labels}")
        return 0

    v1 = client.api.prompts.create(
        request=CreateTextPromptRequest(
            name=PROMPT_NAME,
            prompt=BASELINE_TEMPLATE,
            type="text",
            labels=["baseline", "production"],
            tags=["k4-l3b", "baseline"],
            commit_message="Initial baseline prompt for Monitoring & LLMOps lab",
        )
    )
    v2 = client.api.prompts.create(
        request=CreateTextPromptRequest(
            name=PROMPT_NAME,
            prompt=CANDIDATE_TEMPLATE,
            type="text",
            labels=["candidate"],
            tags=["k4-l3b", "candidate"],
            commit_message="Candidate: answer only from relevant context; avoid unsupported claims",
        )
    )
    print(f"Created {PROMPT_NAME}: v{v1.version} labels={v1.labels}; v{v2.version} labels={v2.labels}")
    print("production stays on baseline; candidate remains labeled for comparison.")
    client.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

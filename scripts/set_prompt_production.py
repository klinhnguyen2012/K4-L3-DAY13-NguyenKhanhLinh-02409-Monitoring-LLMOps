from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Move Langfuse production label to a prompt version")
    parser.add_argument("--version", type=int, required=True, help="Existing prompt version number")
    args = parser.parse_args()
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("Thiếu LANGFUSE_PUBLIC_KEY hoặc LANGFUSE_SECRET_KEY trong môi trường.")
        return 1

    name = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    client = get_client()
    prompt = client.api.prompts.get(name, version=args.version)
    labels = [label for label in prompt.labels if label not in {"production", "latest"}]
    labels.append("production")
    updated = client.api.prompt_version.update(name, args.version, new_labels=labels)
    production = client.api.prompts.get(name, label="production")
    if production.version != args.version:
        raise RuntimeError(f"production resolved to v{production.version}, expected v{args.version}")
    print(f"{name} production -> v{updated.version}; labels={updated.labels}")
    client.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

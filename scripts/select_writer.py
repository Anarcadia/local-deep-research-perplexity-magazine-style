#!/usr/bin/env python3
"""Record the final-report model selected for one research run."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import configure


NOTICE = (
    "如果用户处于OpenAI Anthropic Google可服务国家范围之外，则Openrouter源中目前配置唯一可用的"
    "替代写作模型是GLM-5.2，用户只能选择此模型，或者解除Openrouter账户的限制，又或者自己让AI"
    "改写skill，修改后端模型id为其他可用模型。"
)

CHOICES = {
    "agent": ("agent", None),
    "glm-5.2": ("openrouter", "glm-5.2"),
    "opus-4.6": ("openrouter", "opus-4.6"),
    "sonnet-5": ("openrouter", "sonnet-5"),
    "gemini-3.1-pro-preview": ("openrouter", "gemini-3.1-pro-preview"),
}


def openrouter_ready() -> tuple[bool, str | None]:
    local = configure.read_env()
    if local.get("OPENROUTER_API_KEY"):
        return True, "config/.env.local"
    if os.environ.get("OPENROUTER_API_KEY"):
        return True, "process environment"
    return False, None


def build_selection(choice: str, routing: dict) -> dict:
    if choice not in CHOICES:
        raise ValueError(f"Unknown writing model: {choice}")
    backend, model_choice = CHOICES[choice]
    credential_ready, source = openrouter_ready() if backend == "openrouter" else (True, None)
    if backend == "agent":
        model_id = routing["backends"]["agent"]["model"]
        roles = routing["backends"]["agent"]["roles"]
    else:
        model = routing["backends"]["openrouter"]["models"][model_choice]
        model_id = model["model"]
        roles = model["roles"]
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selection": choice,
        "backend": backend,
        "model_choice": model_choice,
        "model_id": model_id,
        "roles": roles,
        "ready": credential_ready,
        "credential_source": source,
        "notice_shown": NOTICE,
        "warning": None if credential_ready else "OPENROUTER_API_KEY is not configured; this writing route will fail.",
    }


def interactive_choice() -> str:
    print(NOTICE)
    print("\nChoose the final-report writer:")
    print("  A. Current Agent model")
    print("  B. OpenRouter GLM-5.2")
    print("  C. OpenRouter Claude Opus 4.6")
    print("  D. OpenRouter Claude Sonnet 5")
    print("  E. OpenRouter Gemini 3.1 Pro Preview")
    mapping = {
        "A": "agent",
        "B": "glm-5.2",
        "C": "opus-4.6",
        "D": "sonnet-5",
        "E": "gemini-3.1-pro-preview",
    }
    answer = input("Selection: ").strip().upper()
    if answer not in mapping:
        raise ValueError("Use A, B, C, D, or E")
    return mapping[answer]


def main() -> int:
    parser = argparse.ArgumentParser(description="Select the final-report model for one research run")
    parser.add_argument("--select", choices=list(CHOICES))
    parser.add_argument("--output", required=True, help="Run-local writing-selection.json path")
    args = parser.parse_args()
    try:
        choice = args.select or interactive_choice()
        routing = json.loads((configure.SKILL_DIR / "config" / "model-routing.json").read_text(encoding="utf-8"))
        result = build_selection(choice, routing)
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ready"]:
            print("error: selected OpenRouter writer is not configured and its call will fail", file=sys.stderr)
            return 2
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create the per-run optional-provider selection for Local Deep Research."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import configure


ALIASES = {
    "exa": "exa",
    "perplexity": "perplexity",
    "grok": "grok_build",
    "grok_build": "grok_build",
    "kimi": "kimi_code",
    "kimi_code": "kimi_code",
}


def parse_selection(raw: str) -> list[str]:
    value = raw.strip().lower()
    if value == "all":
        return list(configure.OPTIONAL_TOOLS)
    if value in {"none", "off"}:
        return []
    selected: list[str] = []
    for item in value.split(","):
        key = item.strip().replace("-", "_")
        if not key:
            continue
        if key not in ALIASES:
            raise ValueError(f"Unknown provider: {item.strip()}")
        tool_id = ALIASES[key]
        if tool_id not in selected:
            selected.append(tool_id)
    return selected


def readiness(tool_id: str, config: dict, env: dict[str, str]) -> tuple[bool, list[str]]:
    spec = config["tools"][tool_id]
    reasons: list[str] = []
    if not config.get("configured"):
        reasons.append("setup has not been completed")
    if not spec.get("enabled"):
        reasons.append("provider is disabled in config/tools.local.json")
    if not configure.credential_ready(tool_id, env):
        reasons.append("credentials are missing")
    command = spec.get("command")
    if command and not configure.command_ready(command):
        reasons.append(f"command is unavailable: {command}")
    return not reasons, reasons


def build_selection(selected: list[str], config: dict, env: dict[str, str]) -> dict:
    tools = {}
    active: list[str] = []
    unavailable: list[str] = []
    for tool_id in configure.OPTIONAL_TOOLS:
        was_selected = tool_id in selected
        ready, reasons = readiness(tool_id, config, env) if was_selected else (False, [])
        if was_selected and ready:
            active.append(tool_id)
        elif was_selected:
            unavailable.append(tool_id)
        tools[tool_id] = {
            "selected": was_selected,
            "active": was_selected and ready,
            "ready": ready if was_selected else None,
            "reasons": reasons,
            "role": config["tools"][tool_id].get("role"),
        }
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected": selected,
        "active": active,
        "unavailable": unavailable,
        "tools": tools,
        "warning": (
            "Selected providers must be configured before research. "
            "Unavailable provider calls fail instead of silently falling back."
        ),
    }


def interactive_choice() -> str:
    print("Select optional providers for this research run:")
    print("  A. All custom providers")
    print("  B. Exa")
    print("  C. Perplexity")
    print("  D. Grok Build")
    print("  E. KimiCode")
    print("  F. None")
    print("B-E may be combined, for example: B,D,E")
    raw = input("Selection: ").strip().upper()
    if raw == "A":
        return "all"
    if raw in {"F", ""}:
        return "none"
    mapping = {"B": "exa", "C": "perplexity", "D": "grok_build", "E": "kimi_code"}
    choices = [item.strip() for item in raw.split(",") if item.strip()]
    if not choices or any(item not in mapping for item in choices):
        raise ValueError("Use A, F, or a comma-separated combination of B, C, D, E")
    return ",".join(mapping[item] for item in choices)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select optional providers for one research run")
    parser.add_argument("--select", help="all, none, or comma-separated provider IDs")
    parser.add_argument("--output", required=True, help="Run-local tool-selection.json path")
    args = parser.parse_args()

    try:
        raw = args.select if args.select is not None else interactive_choice()
        selected = parse_selection(raw)
        result = build_selection(selected, configure.load_config(), configure.read_env())
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        if result["unavailable"]:
            print(
                "error: selected providers are not configured and their calls will fail: "
                + ", ".join(result["unavailable"]),
                file=sys.stderr,
            )
            return 2
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Interactive provider setup for Local Deep Research."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = SKILL_DIR / "config"
TOOLS_EXAMPLE = CONFIG_DIR / "tools.example.json"
TOOLS_LOCAL = CONFIG_DIR / "tools.local.json"
ENV_EXAMPLE = CONFIG_DIR / ".env.example"
ENV_LOCAL = CONFIG_DIR / ".env.local"

OPTIONAL_TOOLS = ["exa", "perplexity", "grok_build", "kimi_code"]
EXA_HOME = "https://exa.ai/"
EXA_DASHBOARD = "https://dashboard.exa.ai/"
EXA_API_KEYS = "https://dashboard.exa.ai/api-keys"

DISPLAY = {
    "exa": (
        "Exa",
        "Adds semantic search, papers, specialist pages, and domain/date filters.",
        "Without it, specialist and semantically related sources may be missed.",
    ),
    "perplexity": (
        "Perplexity",
        "Adds cited Sonar synthesis and Sonar Deep Research for systematic gaps.",
        "Without it, macro coverage must be assembled from ordinary searches.",
    ),
    "grok_build": (
        "Grok Build",
        "Adds overseas users, grassroots experience, communities, social platforms, and emerging disputes.",
        "Without it, user and social perspectives may be thinner.",
    ),
    "kimi_code": (
        "KimiCode",
        "Adds Chinese domestic policy, markets, platforms, media, industries, creators, and communities.",
        "Without it, China-specific coverage may be incomplete.",
    ),
}


def read_env(path: Path = ENV_LOCAL) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_env(values: dict[str, str], path: Path = ENV_LOCAL) -> None:
    keys = ["EXA_API_KEY", "PERPLEXITY_API_KEY", "XAI_API_KEY", "KIMI_API_KEY", "OPENROUTER_API_KEY"]
    lines = ["# Local secrets for Local-Deep-Research-Perplexity-Magazine-style. Do not commit this file."]
    lines.extend(f"{key}={values.get(key, '')}" for key in keys)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o600)


def load_example(path: Path = TOOLS_EXAMPLE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def initialize_files(config_dir: Path = CONFIG_DIR) -> tuple[Path, Path]:
    config_dir.mkdir(parents=True, exist_ok=True)
    tools_local = config_dir / "tools.local.json"
    env_local = config_dir / ".env.local"
    if not tools_local.exists():
        tools_local.write_text(
            json.dumps(load_example(config_dir / "tools.example.json"), indent=2) + "\n",
            encoding="utf-8",
        )
    if not env_local.exists():
        example_values = read_env(config_dir / ".env.example")
        write_env(example_values, env_local)
    return tools_local, env_local


def load_config(path: Path = TOOLS_LOCAL) -> dict[str, Any]:
    if not path.exists():
        return load_example()
    local = json.loads(path.read_text(encoding="utf-8"))
    merged = load_example()
    merged.update({key: value for key, value in local.items() if key != "tools"})
    for tool_id, spec in local.get("tools", {}).items():
        if tool_id in merged["tools"]:
            merged["tools"][tool_id].update(spec)
        else:
            merged["tools"][tool_id] = spec
    return merged


def command_ready(command: str | None) -> bool:
    return bool(command and shutil.which(command))


def credential_ready(tool_id: str, env: dict[str, str]) -> bool:
    if tool_id == "exa":
        return bool(env.get("EXA_API_KEY"))
    if tool_id == "perplexity":
        return bool(env.get("PERPLEXITY_API_KEY"))
    if tool_id == "grok_build":
        return bool(env.get("XAI_API_KEY") or (Path.home() / ".grok" / "auth.json").exists())
    if tool_id == "kimi_code":
        return bool(
            env.get("KIMI_API_KEY")
            or (Path.home() / ".kimi-code" / "credentials" / "kimi-code.json").exists()
        )
    return True


def status(config: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "configured": bool(config.get("configured")),
        "config_file": str(TOOLS_LOCAL),
        "key_file": str(ENV_LOCAL),
        "tools": {},
        "writing_backends": {
            "agent": {
                "ready": True,
                "execution": "host-native",
            },
            "openrouter": {
                "ready": bool(env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")),
                "credential_ready": bool(env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")),
                "credential_source": (
                    str(ENV_LOCAL) if env.get("OPENROUTER_API_KEY")
                    else "process environment" if os.environ.get("OPENROUTER_API_KEY")
                    else None
                ),
            }
        },
    }
    for tool_id, spec in config["tools"].items():
        enabled = bool(spec.get("enabled"))
        command = spec.get("command")
        result["tools"][tool_id] = {
            "enabled": enabled,
            "command_available": command_ready(command) if command else None,
            "credential_ready": credential_ready(tool_id, env) if enabled else None,
            "role": spec.get("role"),
        }
    return result


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {suffix} ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


def hidden_key(label: str, current: str) -> str:
    note = " (press Enter to keep the existing value)" if current else ""
    value = getpass.getpass(f"{label}{note}: ").strip()
    return value or current


def maybe_login(command: str) -> None:
    if not command_ready(command):
        print(f"  Command '{command}' was not found. Install the CLI, then run: {command} login")
        return
    if ask_yes_no(f"  Run '{command} login' now?", default=False):
        subprocess.run([command, "login"], check=False)


def configure_cli_auth(tool_id: str, env: dict[str, str]) -> None:
    if tool_id == "grok_build":
        print("  Authentication: OAuth/device login is recommended; XAI_API_KEY is also supported.")
        mode = input("  Choose [login/api/skip] (default login): ").strip().lower() or "login"
        if mode == "api":
            env["XAI_API_KEY"] = hidden_key("  XAI_API_KEY", env.get("XAI_API_KEY", ""))
        elif mode == "login":
            maybe_login("grok")
    else:
        print("  Authentication: KimiCode device login is recommended; custom adapters may use KIMI_API_KEY.")
        mode = input("  Choose [login/api/skip] (default login): ").strip().lower() or "login"
        if mode == "api":
            env["KIMI_API_KEY"] = hidden_key("  KIMI_API_KEY", env.get("KIMI_API_KEY", ""))
        elif mode == "login":
            maybe_login("kimi")


def interactive_setup() -> None:
    initialize_files()
    config = load_config()
    env = read_env()

    print("Welcome to Local-Deep-Research-Perplexity-Magazine-style.\n")
    print(
        "If your Agent has no native web search or weak web-search results, "
        "configure Exa before research. Exa has a free search allowance and is strongly recommended."
    )
    print("The current official free tier advertises up to 20,000 requests per month; terms may change.")
    print(f"Exa: {EXA_HOME}")
    print(f"Register or sign in: {EXA_DASHBOARD}")
    print(f"Create an API key: {EXA_API_KEYS}")
    print(f"Write EXA_API_KEY=<key> to: {ENV_LOCAL}")
    print("Do not paste API keys into an Agent chat.\n")
    print("Local Deep Research optional provider setup\n")
    print("Built-in host web search remains enabled. Optional providers are disabled by default.\n")

    for tool_id in OPTIONAL_TOOLS:
        name, benefit, disabled_effect = DISPLAY[tool_id]
        print(f"{name}\n  Enabled: {benefit}\n  Disabled: {disabled_effect}")
        enabled = ask_yes_no(f"Enable {name}?", default=config["tools"][tool_id]["enabled"])
        config["tools"][tool_id]["enabled"] = enabled
        if not enabled:
            print()
            continue
        if tool_id == "exa":
            env["EXA_API_KEY"] = hidden_key("  EXA_API_KEY", env.get("EXA_API_KEY", ""))
        elif tool_id == "perplexity":
            env["PERPLEXITY_API_KEY"] = hidden_key(
                "  PERPLEXITY_API_KEY", env.get("PERPLEXITY_API_KEY", "")
            )
        else:
            configure_cli_auth(tool_id, env)
        print()

    print("OpenRouter writing backend\n  Enables direct OpenAI-compatible final-report generation.")
    if ask_yes_no("Configure an OpenRouter API key?", default=bool(env.get("OPENROUTER_API_KEY"))):
        env["OPENROUTER_API_KEY"] = hidden_key(
            "  OPENROUTER_API_KEY", env.get("OPENROUTER_API_KEY", "")
        )
    print()

    config["configured"] = True
    TOOLS_LOCAL.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    write_env(env)
    print(f"Provider switches: {TOOLS_LOCAL}")
    print(f"API keys: {ENV_LOCAL}")
    print("Run 'python3 scripts/configure.py --status' to verify the setup.")


def enable_tools(ids: list[str]) -> None:
    initialize_files()
    config = load_config()
    unknown = sorted(set(ids) - set(OPTIONAL_TOOLS))
    if unknown:
        raise ValueError(f"Unknown providers: {', '.join(unknown)}")
    for tool_id in OPTIONAL_TOOLS:
        config["tools"][tool_id]["enabled"] = tool_id in ids
    config["configured"] = True
    TOOLS_LOCAL.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Provider switches written to {TOOLS_LOCAL}")
    print(f"Fill API keys in {ENV_LOCAL}; use 'grok login' and 'kimi login' for CLI login.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure optional Local Deep Research providers")
    parser.add_argument("--status", action="store_true", help="Show provider readiness without secrets")
    parser.add_argument("--json", action="store_true", help="Use JSON with --status")
    parser.add_argument("--init", action="store_true", help="Create disabled local config files")
    parser.add_argument("--enable", help="Comma-separated provider IDs: exa,perplexity,grok_build,kimi_code")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.init:
            tools_file, env_file = initialize_files()
            print(f"Created/kept provider switches: {tools_file}")
            print(f"Created/kept API key file: {env_file}")
            return 0
        if args.enable is not None:
            enable_tools([item.strip() for item in args.enable.split(",") if item.strip()])
            return 0
        if args.status:
            current = status(load_config(), read_env())
            if args.json:
                print(json.dumps(current, indent=2))
            else:
                print(f"Configured: {current['configured']}")
                print(f"Provider switches: {current['config_file']}")
                print(f"API keys: {current['key_file']}")
                for tool_id, item in current["tools"].items():
                    print(
                        f"- {tool_id}: enabled={item['enabled']} "
                        f"command={item['command_available']} credentials={item['credential_ready']}"
                    )
            return 0
        interactive_setup()
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

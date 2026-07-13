#!/usr/bin/env python3
"""Route final report writing to Codex or OpenRouter."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import configure


SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_DIR / "config" / "model-routing.json"
ENV_PATH = SKILL_DIR / "config" / ".env.local"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_backend(config: dict, requested: str | None) -> tuple[str, dict]:
    name = requested or config["default_backend"]
    if name not in config["backends"]:
        raise ValueError(f"Unknown backend: {name}")
    return name, config["backends"][name]


def resolve_model(name: str, spec: dict, requested: str | None) -> tuple[str | None, dict]:
    if name == "agent":
        return None, dict(spec)
    choice = requested or spec["default_model_choice"]
    if choice not in spec["models"]:
        raise ValueError(f"Unknown OpenRouter model choice: {choice}")
    resolved = dict(spec)
    resolved.update(spec["models"][choice])
    return choice, resolved


def openrouter_key() -> tuple[str, str | None]:
    local = configure.read_env()
    if local.get("OPENROUTER_API_KEY"):
        return local["OPENROUTER_API_KEY"], str(ENV_PATH)
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"], "process environment"
    return "", None


def route_status(name: str, spec: dict) -> dict[str, Any]:
    if name == "agent":
        return {
            "backend": name,
            "ready": True,
            "model": spec["model"],
            "execution": "host-native",
            "roles": spec["roles"],
        }
    key, source = openrouter_key()
    return {
        "backend": name,
        "ready": bool(key),
        "credential_ready": bool(key),
        "credential_source": source,
        "base_url": spec["base_url"],
        "model": spec["model"],
        "reasoning_effort": spec.get("reasoning_effort"),
        "roles": spec.get("roles", []),
        "key_file": str(ENV_PATH),
    }


def apply_default_style(config: dict, prompt: str, style_mode: str) -> str:
    composition = f"写作结构契约：\n{config['composition_contract']}\n\n"
    if style_mode == "explicit":
        return f"{composition}任务：\n{prompt}"
    return (
        f"写作风格要求：\n{config['default_writing_style']}\n"
        f"{config['default_language_conventions']}\n\n{composition}任务：\n{prompt}"
    )


def apply_audit_contract(config: dict, prompt: str) -> str:
    return f"独立审计要求：\n{config['audit_contract']}\n\n任务：\n{prompt}"


def bundle_context(config: dict, cwd: Path, prompt: str, task: str = "writing") -> str:
    sections = [prompt]
    field = "audit_context_files" if task == "audit" else "context_files"
    for filename in config.get(field, []):
        path = cwd / filename
        if path.is_file():
            sections.append(f"\n\n---\n\n# Research artifact: {filename}\n\n{path.read_text(encoding='utf-8')}")
    return "".join(sections)


def require_role(spec: dict, task: str) -> None:
    role = "independent_audit" if task == "audit" else "report_writing"
    if role not in spec.get("roles", []):
        raise ValueError(f"Model {spec['model']} is not configured for {task}")


def openrouter_payload(spec: dict, prompt: str, max_tokens: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": spec["model"],
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    if spec.get("reasoning_effort"):
        payload["reasoning"] = {"effort": spec["reasoning_effort"]}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    return payload


def openrouter_request(spec: dict, prompt: str, max_tokens: int | None = None) -> dict[str, Any]:
    key, _ = openrouter_key()
    if not key:
        raise ValueError(f"OpenRouter API key is missing. Fill {ENV_PATH} or set OPENROUTER_API_KEY")
    request = urllib.request.Request(
        f"{spec['base_url'].rstrip('/')}/chat/completions",
        data=json.dumps(openrouter_payload(spec, prompt, max_tokens)).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-OpenRouter-Title": spec.get(
                "app_title", "Local-Deep-Research-Perplexity-Magazine-style"
            ),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=spec.get("timeout_seconds", 1800)) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1500]
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc


def response_text(data: dict[str, Any]) -> str:
    try:
        message = data["choices"][0]["message"]
        content = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"OpenRouter returned no message content: {json.dumps(data)[:1000]}") from exc
    if content is None and message.get("reasoning"):
        raise RuntimeError("OpenRouter used the completion allowance for reasoning and returned no final text; increase max_tokens")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict))
    raise RuntimeError("OpenRouter returned an unsupported message format")


def run_backend(
    name: str,
    spec: dict,
    cwd: Path,
    prompt_file: Path,
    output: Path,
    style_mode: str,
    config: dict,
    task: str = "writing",
    dry_run: bool = False,
) -> None:
    cwd = cwd.resolve()
    prompt_file = prompt_file.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    base_prompt = prompt_file.read_text(encoding="utf-8")
    require_role(spec, task)
    bundled = bundle_context(config, cwd, base_prompt, task)
    effective = apply_audit_contract(config, bundled) if task == "audit" else apply_default_style(config, bundled, style_mode)

    if dry_run:
        print(json.dumps({
            "backend": name,
            "model": spec["model"],
            "task": task,
            "context_files": [
                filename for filename in config.get(
                    "audit_context_files" if task == "audit" else "context_files", []
                ) if (cwd / filename).is_file()
            ],
            "prompt_characters": len(effective),
        }, ensure_ascii=False, indent=2))
        return

    temporary = output.with_name(f".{output.name}.routing.tmp")
    if temporary.exists():
        temporary.unlink()
    if name == "agent":
        raise ValueError("The current Agent model writes in the host session; do not call the API router for this selection")
    temporary.write_text(response_text(openrouter_request(spec, effective)), encoding="utf-8")
    temporary.replace(output)


def smoke(name: str, spec: dict) -> None:
    if name == "agent":
        print(json.dumps({"ok": True, "backend": name, "model": spec["model"], "execution": "host-native"}))
        return
    data = openrouter_request(spec, "只输出 ROUTE_OK，不要添加其他内容。", max_tokens=256)
    print(json.dumps({
        "ok": "ROUTE_OK" in response_text(data),
        "backend": name,
        "requested_model": spec["model"],
        "response_model": data.get("model"),
        "usage": data.get("usage", {}),
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Route final report writing or auditing to the host Agent or OpenRouter")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    run = sub.add_parser("run")
    smoke_parser = sub.add_parser("smoke")
    for item in (check, run, smoke_parser):
        item.add_argument("--backend", choices=["agent", "openrouter"])
        item.add_argument("--model-choice")
    run.add_argument("--cwd", type=Path, required=True)
    run.add_argument("--prompt-file", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--style-mode", choices=["default", "explicit"], default="default")
    run.add_argument("--task", choices=["writing", "audit"], default="writing")
    args = parser.parse_args()

    try:
        config = load_config()
        name, backend = resolve_backend(config, args.backend)
        choice, spec = resolve_model(name, backend, args.model_choice)
        if args.command == "check":
            result = route_status(name, spec)
            result["model_choice"] = choice
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "run":
            run_backend(
                name, spec, args.cwd, args.prompt_file, args.output,
                args.style_mode, config, args.task, args.dry_run,
            )
        else:
            smoke(name, spec)
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

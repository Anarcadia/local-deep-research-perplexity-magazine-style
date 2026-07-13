#!/usr/bin/env python3
"""Unified optional-provider runner for Local Deep Research."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import configure


def load_selection(path: str, tool_id: str) -> dict:
    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    item = data.get("tools", {}).get(tool_id, {})
    if not item.get("active"):
        reasons = "; ".join(item.get("reasons", [])) or "not selected for this run"
        raise ValueError(f"{tool_id} is unavailable: {reasons}")
    return data


def runtime_env() -> dict[str, str]:
    values = os.environ.copy()
    values.update({key: value for key, value in configure.read_env().items() if value})
    return values


def api_json(method: str, url: str, key: str, payload: dict | None = None, timeout: int = 180) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network request failed: {exc.reason}") from exc


def api_sse(url: str, key: str, payload: dict, timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )
    content: list[str] = []
    result: dict[str, Any] = {}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                value = line[5:].strip()
                if value == "[DONE]":
                    break
                try:
                    chunk = json.loads(value)
                except json.JSONDecodeError:
                    continue
                for choice in chunk.get("choices", []) or []:
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        content.append(piece)
                for key_name in ("citations", "search_results", "related_questions", "usage", "model"):
                    if chunk.get(key_name):
                        result[key_name] = chunk[key_name]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network request failed: {exc.reason}") from exc
    result["choices"] = [{"message": {"content": "".join(content)}}]
    return result


def write_result(data: Any, output: str | None) -> None:
    rendered = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered.rstrip() + "\n", encoding="utf-8")
    else:
        print(rendered)


def exa_search(args, env: dict[str, str]) -> dict:
    payload: dict[str, Any] = {
        "query": args.query,
        "numResults": args.num_results,
        "contents": {"text": {"maxCharacters": args.max_characters}},
    }
    if args.category:
        payload["category"] = args.category
    if args.include_domain:
        payload["includeDomains"] = args.include_domain
    if args.start_date:
        payload["startPublishedDate"] = args.start_date
    if args.end_date:
        payload["endPublishedDate"] = args.end_date
    key = env.get("EXA_API_KEY", "")
    request = urllib.request.Request(
        "https://api.exa.ai/search",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"x-api-key": key, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network request failed: {exc.reason}") from exc


def sonar(args, env: dict[str, str]) -> dict:
    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.query}],
        "return_citations": True,
        "return_images": False,
    }
    if args.recency:
        payload["search_recency_filter"] = args.recency
    if args.domain:
        payload["search_domain_filter"] = args.domain
    options: dict[str, str] = {}
    if args.mode != "fast":
        options["search_type"] = args.mode
    if args.context:
        options["search_context_size"] = args.context
    if options:
        payload["web_search_options"] = options
    if args.mode == "pro":
        payload["stream"] = True
        return api_sse(
            "https://api.perplexity.ai/chat/completions",
            env.get("PERPLEXITY_API_KEY", ""),
            payload,
            args.timeout,
        )
    return api_json(
        "POST",
        "https://api.perplexity.ai/chat/completions",
        env.get("PERPLEXITY_API_KEY", ""),
        payload,
        args.timeout,
    )


def deep_submit(args, env: dict[str, str]) -> dict:
    request_body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.query}],
        "return_citations": True,
        "return_images": False,
    }
    if args.recency:
        request_body["search_recency_filter"] = args.recency
    return api_json(
        "POST",
        "https://api.perplexity.ai/async/chat/completions",
        env.get("PERPLEXITY_API_KEY", ""),
        {"request": request_body},
        args.timeout,
    )


def deep_check(args, env: dict[str, str]) -> dict:
    return api_json(
        "GET",
        f"https://api.perplexity.ai/async/chat/completions/{args.job_id}",
        env.get("PERPLEXITY_API_KEY", ""),
        timeout=args.timeout,
    )


def deep_wait(args, env: dict[str, str]) -> dict:
    deadline = time.time() + args.wait_timeout
    while time.time() < deadline:
        data = deep_check(args, env)
        status = str(data.get("status", "")).upper()
        if status == "COMPLETED":
            return data
        if status in {"FAILED", "CANCELLED", "ERROR"}:
            raise RuntimeError(f"Deep Research ended with status {status}")
        time.sleep(args.interval)
    raise RuntimeError(f"Deep Research did not complete within {args.wait_timeout} seconds")


def run_cli(tool_id: str, args, env: dict[str, str], config: dict) -> str:
    spec = config["tools"][tool_id]
    command = spec["command"]
    if tool_id == "grok_build":
        invocation = [
            command,
            "--agent", spec.get("agent") or "quick-search",
            "--output-format", "plain",
            "--no-memory",
            "--no-subagents",
            "--single", args.query,
        ]
    else:
        invocation = [command, "--prompt", args.query, "--output-format", "text"]
    with tempfile.TemporaryDirectory(prefix="local-deep-research-") as clean_cwd:
        completed = subprocess.run(
            invocation,
            cwd=args.cwd or clean_cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"{command} exited with {completed.returncode}")
    return completed.stdout


def add_common(parser: argparse.ArgumentParser, tool_id: str) -> None:
    parser.set_defaults(tool_id=tool_id)
    parser.add_argument("--selection", required=True, help="Run-local tool-selection.json")
    parser.add_argument("--output", help="Write raw provider output to this file")
    parser.add_argument("--timeout", type=int, default=180)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run configured optional research providers")
    sub = parser.add_subparsers(dest="command", required=True)

    exa = sub.add_parser("exa-search")
    exa.add_argument("query")
    exa.add_argument("--num-results", type=int, default=10)
    exa.add_argument("--max-characters", type=int, default=4000)
    exa.add_argument("--category")
    exa.add_argument("--include-domain", action="append")
    exa.add_argument("--start-date")
    exa.add_argument("--end-date")
    add_common(exa, "exa")

    sonar_parser = sub.add_parser("sonar")
    sonar_parser.add_argument("query")
    sonar_parser.add_argument("--model", default="sonar-pro")
    sonar_parser.add_argument("--mode", choices=["fast", "pro", "auto"], default="fast")
    sonar_parser.add_argument("--context", choices=["low", "medium", "high"])
    sonar_parser.add_argument("--recency", choices=["hour", "day", "week", "month", "year"])
    sonar_parser.add_argument("--domain", action="append")
    add_common(sonar_parser, "perplexity")

    submit = sub.add_parser("deep-submit")
    submit.add_argument("query")
    submit.add_argument("--model", default="sonar-deep-research")
    submit.add_argument("--recency", choices=["hour", "day", "week", "month", "year"])
    add_common(submit, "perplexity")

    for name in ("deep-check", "deep-wait"):
        deep = sub.add_parser(name)
        deep.add_argument("job_id")
        if name == "deep-wait":
            deep.add_argument("--wait-timeout", type=int, default=1800)
            deep.add_argument("--interval", type=int, default=15)
        add_common(deep, "perplexity")

    for name, tool_id in (("grok-search", "grok_build"), ("kimi-search", "kimi_code")):
        cli = sub.add_parser(name)
        cli.add_argument("query")
        cli.add_argument("--cwd", help="Explicit workspace; defaults to an isolated temporary directory")
        add_common(cli, tool_id)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        load_selection(args.selection, args.tool_id)
        env = runtime_env()
        config = configure.load_config()
        handlers = {
            "exa-search": lambda: exa_search(args, env),
            "sonar": lambda: sonar(args, env),
            "deep-submit": lambda: deep_submit(args, env),
            "deep-check": lambda: deep_check(args, env),
            "deep-wait": lambda: deep_wait(args, env),
            "grok-search": lambda: run_cli("grok_build", args, env, config),
            "kimi-search": lambda: run_cli("kimi_code", args, env, config),
        }
        write_result(handlers[args.command](), args.output)
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

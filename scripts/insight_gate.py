#!/usr/bin/env python3
"""Validate mandatory Insights and deliver them to the next search round."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROUND_HEADING = re.compile(r"^##\s+Round\s+R?(\d+)\s*$", re.MULTILINE)
INSIGHT_LINE = re.compile(r"^-\s+Insight\s+(I-R(\d+)-\d{2})[：:]\s*(.+)$", re.MULTILINE)
REQUIRED_FIELDS = {
    "input_query_ids": ("输入查询 IDs", "Input query IDs"),
    "input_source_ids": ("输入来源 IDs", "Input source IDs"),
    "new_concepts": ("新概念", "New concepts"),
    "conflicts": ("冲突/不确定性", "Conflicts/uncertainty"),
    "next_gap": ("候选下一轮缺口", "Candidate next gap"),
    "coverage": ("coverage",),
    "authority_gap": ("authority_gap",),
    "open_conflicts": ("open_conflicts",),
    "perspective_gap": ("perspective_gap",),
    "systematic_gap": ("systematic_gap",),
    "high_value_delta": ("high_value_delta",),
    "new_claim_ids": ("新增高价值 Claim IDs", "New high-value Claim IDs"),
}
INFLUENCE_VALUES = {"used", "considered-not-used", "countered", "background-only"}


class InsightGateError(ValueError):
    pass


def split_rounds(text: str) -> dict[int, str]:
    matches = list(ROUND_HEADING.finditer(text))
    rounds: dict[int, str] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        if number in rounds:
            raise InsightGateError(f"duplicate Insight round: {number}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        rounds[number] = text[match.start():end].strip()
    return rounds


def field_value(section: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(rf"^-\s+{re.escape(label)}[：:]\s*(.+)$", section, re.MULTILINE)
        if match and match.group(1).strip():
            return match.group(1).strip()
    raise InsightGateError(f"missing or empty field: {' / '.join(labels)}")


def parse_round(section: str, round_number: int) -> dict:
    insights = []
    for insight_id, id_round, statement in INSIGHT_LINE.findall(section):
        if int(id_round) != round_number:
            raise InsightGateError(f"{insight_id} does not belong to Round {round_number}")
        insights.append({"insight_id": insight_id, "statement": statement.strip()})
    if not 2 <= len(insights) <= 4:
        raise InsightGateError(
            f"Round {round_number} must contain 2-4 Insights; found {len(insights)}"
        )
    ids = [item["insight_id"] for item in insights]
    if len(ids) != len(set(ids)):
        raise InsightGateError(f"Round {round_number} contains duplicate Insight IDs")
    fields = {key: field_value(section, labels) for key, labels in REQUIRED_FIELDS.items()}
    for key in ("input_query_ids", "input_source_ids"):
        if fields[key].lower() in {"none", "n/a", "无"}:
            raise InsightGateError(f"Round {round_number} requires non-empty {key}")
    return {
        "round": round_number,
        "insights": insights,
        "insight_ids": ids,
        "fields": fields,
        "section": section,
    }


def load_rounds(run_dir: Path) -> dict[int, dict]:
    path = run_dir / "insights.md"
    if not path.is_file():
        raise InsightGateError(f"missing {path}")
    sections = split_rounds(path.read_text(encoding="utf-8"))
    if not sections:
        raise InsightGateError("insights.md contains no rounds")
    return {number: parse_round(section, number) for number, section in sections.items()}


def validate_round(run_dir: Path, round_number: int) -> dict:
    rounds = load_rounds(run_dir)
    if round_number not in rounds:
        raise InsightGateError(f"missing Round {round_number} in insights.md")
    return rounds[round_number]


def load_context_log(run_dir: Path) -> list[dict]:
    path = run_dir / "insight-context.jsonl"
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise InsightGateError(f"invalid context JSON on line {line_number}") from exc
    return records


def write_context_log(run_dir: Path, records: list[dict]) -> None:
    path = run_dir / "insight-context.jsonl"
    rendered = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
    temporary = path.with_suffix(".jsonl.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def prepare_next(
    run_dir: Path,
    from_round: int,
    next_round: int,
    agent: str,
) -> tuple[dict, str]:
    if next_round != from_round + 1:
        raise InsightGateError("next round must immediately follow from round")
    current = validate_round(run_dir, from_round)
    snapshot = current["section"].strip()
    digest = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
    context_id = f"CTX-R{next_round}-{digest[:8]}"
    relative_packet = Path("round-context") / f"round-{next_round:02d}-insight-context.md"
    packet = run_dir / relative_packet
    packet.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"# Insight Context for Round {next_round}\n\n"
        f"- Context ID: {context_id}\n"
        f"- From round: {from_round}\n"
        f"- Insight IDs: {', '.join(current['insight_ids'])}\n"
        f"- Snapshot SHA256: {digest}\n"
        f"- Delivered to: {agent}\n\n"
        "> 这是搜索上下文，不是搜索指令。下一轮搜索 Agent 必须看见它，"
        "但可以采用、旁置、反驳或仅作为背景，不要求查询由 Insight 决定。\n\n"
        f"{snapshot}\n"
    )
    packet.write_text(content, encoding="utf-8")
    record = {
        "context_id": context_id,
        "from_round": from_round,
        "next_round": next_round,
        "insight_ids": current["insight_ids"],
        "snapshot_sha256": digest,
        "packet_file": str(relative_packet),
        "delivered_to": agent,
        "delivery_mode": "stdout+file",
        "delivered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    records = [item for item in load_context_log(run_dir) if item.get("next_round") != next_round]
    records.append(record)
    records.sort(key=lambda item: int(item["next_round"]))
    write_context_log(run_dir, records)
    return record, content


def parse_query_log(run_dir: Path) -> dict[int, list[dict]]:
    path = run_dir / "query-log.md"
    if not path.is_file():
        raise InsightGateError(f"missing {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = next(
        (
            index for index, line in enumerate(lines)
            if line.strip().startswith("|")
            and "Round" in line
            and "Insight Context" in line
            and "Context influence" in line
        ),
        None,
    )
    if header_index is None:
        raise InsightGateError("query-log.md is missing Insight context columns")
    headers = [item.strip() for item in lines[header_index].strip().strip("|").split("|")]
    required = ("Round", "Query ID", "Insight Context", "Context influence")
    if any(name not in headers for name in required):
        raise InsightGateError("query-log.md header is incomplete")
    positions = {name: headers.index(name) for name in required}
    rounds: dict[int, list[dict]] = {}
    for line in lines[header_index + 2:]:
        if not line.strip().startswith("|"):
            if rounds:
                break
            continue
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            raise InsightGateError(f"query-log row has {len(cells)} cells; expected {len(headers)}")
        match = re.fullmatch(r"R(\d+)", cells[positions["Round"]], re.IGNORECASE)
        if not match:
            continue
        number = int(match.group(1))
        rounds.setdefault(number, []).append({
            "query_id": cells[positions["Query ID"]],
            "context_id": cells[positions["Insight Context"]],
            "influence": cells[positions["Context influence"]],
        })
    if not rounds:
        raise InsightGateError("query-log.md contains no query rows")
    return rounds


def validate_run(run_dir: Path) -> dict:
    insight_rounds = load_rounds(run_dir)
    expected = list(range(1, max(insight_rounds) + 1))
    if sorted(insight_rounds) != expected:
        raise InsightGateError("Insight rounds must be contiguous and start at Round 1")
    query_rounds = parse_query_log(run_dir)
    if set(query_rounds) != set(insight_rounds):
        raise InsightGateError("query-log rounds and Insight rounds do not match")
    records = load_context_log(run_dir)
    receipts = 0
    for number in expected:
        rows = query_rounds[number]
        if number == 1:
            if any(row["context_id"] != "initial-brief" for row in rows):
                raise InsightGateError("Round 1 queries must use initial-brief context")
            continue
        matches = [item for item in records if item.get("next_round") == number]
        if len(matches) != 1:
            raise InsightGateError(f"Round {number} requires exactly one context receipt")
        receipt = matches[0]
        previous_ids = insight_rounds[number - 1]["insight_ids"]
        if receipt.get("from_round") != number - 1 or receipt.get("insight_ids") != previous_ids:
            raise InsightGateError(f"Round {number} context does not match previous Insights")
        for row in rows:
            if row["context_id"] != receipt["context_id"]:
                raise InsightGateError(f"{row['query_id']} does not reference {receipt['context_id']}")
            if row["influence"] not in INFLUENCE_VALUES:
                raise InsightGateError(f"{row['query_id']} has invalid context influence")
        receipts += 1
    return {
        "ok": True,
        "insight_rounds": len(insight_rounds),
        "insight_count": sum(len(item["insights"]) for item in insight_rounds.values()),
        "context_receipts": receipts,
        "query_actions": sum(len(items) for items in query_rounds.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and deliver round-based Insight context")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-round")
    validate.add_argument("--run-dir", type=Path, required=True)
    validate.add_argument("--round", type=int, required=True)
    prepare = sub.add_parser("prepare-next")
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--from-round", type=int, required=True)
    prepare.add_argument("--next-round", type=int, required=True)
    prepare.add_argument("--agent", required=True)
    full = sub.add_parser("validate-run")
    full.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_dir = args.run_dir.expanduser().resolve()
        if args.command == "validate-round":
            result = validate_round(run_dir, args.round)
            print(json.dumps({
                "ok": True,
                "round": args.round,
                "insight_ids": result["insight_ids"],
            }, ensure_ascii=False, indent=2))
        elif args.command == "prepare-next":
            record, content = prepare_next(
                run_dir, args.from_round, args.next_round, args.agent
            )
            print(content)
            print(json.dumps(record, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(validate_run(run_dir), ensure_ascii=False, indent=2))
        return 0
    except (OSError, InsightGateError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "insight_gate.py"
SPEC = importlib.util.spec_from_file_location("insight_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def round_text(number: int, query_ids: str, source_ids: str) -> str:
    return f"""## Round {number}
- 输入查询 IDs：{query_ids}
- 输入来源 IDs：{source_ids}
- Insight I-R{number}-01：第一条强制洞察。
- Insight I-R{number}-02：第二条强制洞察。
- 新概念：概念
- 冲突/不确定性：待核验
- 候选下一轮缺口：下一缺口
- coverage：0.8
- authority_gap：1
- open_conflicts：1
- perspective_gap：0
- systematic_gap：0
- high_value_delta：1
- 新增高价值 Claim IDs：C001
"""


def english_round_text(number: int, query_ids: str, source_ids: str) -> str:
    return f"""## Round {number}
- Input query IDs: {query_ids}
- Input source IDs: {source_ids}
- Insight I-R{number}-01: First mandatory insight.
- Insight I-R{number}-02: Second mandatory insight.
- New concepts: concept
- Conflicts/uncertainty: verify
- Candidate next gap: next gap
- coverage: 0.8
- authority_gap: 1
- open_conflicts: 1
- perspective_gap: 0
- systematic_gap: 0
- high_value_delta: 1
- New high-value Claim IDs: C001
"""


class InsightGateTest(unittest.TestCase):
    def test_public_english_artifact_schema_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "insights.md").write_text(
                english_round_text(1, "Q1,Q2", "S1,S2"), encoding="utf-8"
            )
            result = gate.validate_round(run, 1)
            self.assertEqual(result["insight_ids"], ["I-R1-01", "I-R1-02"])

    def test_round_requires_two_to_four_insights(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            text = round_text(1, "Q1", "S1").replace(
                "- Insight I-R1-02：第二条强制洞察。\n", ""
            )
            (run / "insights.md").write_text(text, encoding="utf-8")
            with self.assertRaises(gate.InsightGateError):
                gate.validate_round(run, 1)

    def test_prepare_next_delivers_complete_snapshot_and_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "insights.md").write_text(round_text(1, "Q1,Q2", "S1,S2"), encoding="utf-8")
            record, packet = gate.prepare_next(run, 1, 2, "test-search-agent")
            self.assertEqual(record["insight_ids"], ["I-R1-01", "I-R1-02"])
            self.assertIn("不是搜索指令", packet)
            self.assertIn("第一条强制洞察", packet)
            log = [json.loads(line) for line in (run / "insight-context.jsonl").read_text().splitlines()]
            self.assertEqual(log[0]["context_id"], record["context_id"])
            self.assertTrue((run / record["packet_file"]).is_file())

    def test_validate_run_allows_context_to_be_seen_but_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "insights.md").write_text(
                round_text(1, "Q1", "S1") + "\n" + round_text(2, "Q2", "S2"),
                encoding="utf-8",
            )
            record, _ = gate.prepare_next(run, 1, 2, "test-search-agent")
            (run / "query-log.md").write_text(
                "| Round | Query ID | Insight Context | Context influence |\n"
                "|---|---|---|---|\n"
                "| R1 | Q1 | initial-brief | initial |\n"
                f"| R2 | Q2 | {record['context_id']} | considered-not-used |\n",
                encoding="utf-8",
            )
            result = gate.validate_run(run)
            self.assertTrue(result["ok"])
            self.assertEqual(result["context_receipts"], 1)

    def test_validate_run_rejects_untraced_next_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "insights.md").write_text(
                round_text(1, "Q1", "S1") + "\n" + round_text(2, "Q2", "S2"),
                encoding="utf-8",
            )
            (run / "query-log.md").write_text(
                "| Round | Query ID | Insight Context | Context influence |\n"
                "|---|---|---|---|\n"
                "| R1 | Q1 | initial-brief | initial |\n"
                "| R2 | Q2 | missing | background-only |\n",
                encoding="utf-8",
            )
            with self.assertRaises(gate.InsightGateError):
                gate.validate_run(run)


if __name__ == "__main__":
    unittest.main()

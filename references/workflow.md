# Workflow

## Initialization

1. Check provider status with `python3 scripts/configure.py --status --json`.
2. Explicitly ask which optional providers to activate for this run: all, any combination of Exa/Perplexity/Grok Build/KimiCode, or none. Warn that selecting an unconfigured tool makes that provider call fail.
3. Write the answer to `<run-dir>/tool-selection.json` with `scripts/select_tools.py`. Stop and offer setup if a selected provider is unavailable.
4. Show the required OpenRouter service-region notice, then explicitly ask whether the current Agent or one configured OpenRouter model should write the report.
5. Write the answer to `<run-dir>/writing-selection.json` with `scripts/select_writer.py`. An OpenRouter choice without a configured key fails; do not silently substitute another model.
6. Create the remaining run artifacts, including `insight-context.jsonl` and `round-context/`.
7. Record the user request, constraints, active providers, inactive-provider effects, and writing route in `brief.md`.
8. Create 4–10 research questions and an external-perspective coverage table.

## Initial Packs

Run Pack A and Pack B. Each pack covers authoritative evidence, relationships/mechanisms, and counterarguments/gaps. One query can be executed by multiple enabled providers when their indexes or perspectives differ.

Plan provider use by information need:

- Exa actively for specialist, semantic, paper, domain-filtered, or long-tail discovery.
- Perplexity Sonar for a cited synthetic pass over relationships or the research terrain.
- KimiCode at least once during the initial packs when Chinese domestic information may be relevant.
- Grok Build at least once during the initial packs when overseas users, grassroots experience, communities, or social platforms may be relevant.

When the boundary is uncertain, favor including the relevant active provider rather than waiting for mainstream search to fail.

Log the round, exact query, provider, time, result count, source IDs, Insight Context ID, context influence state, and intent. Round 1 uses `initial-brief`.

## Systematic Gap Gate

After Pack A and Pack B, set:

```text
coverage = covered required questions / all required questions
authority_gap = core claims without a read A/B source
open_conflicts = unresolved major conflicts
perspective_gap = applicable external perspectives not covered
systematic_gap = incomplete or fragmented overall picture (0/1)
```

If any important gap remains and Perplexity is active for the run, Sonar Deep Research is mandatory. Extract claims and URLs, deduplicate them, and keep their state as `discovered` until the original page is read.

If Perplexity is disabled, create targeted replacement queries and record `sonar_deep_unavailable` in `run-summary.md`.

## Candidate Pool and Reading

For each candidate:

1. Normalize the URL and remove tracking parameters.
2. Deduplicate by URL, title, and content fingerprint.
3. Record source grade, language, date, research questions, discovery query, and state.
4. Read selected sources in full and save an evidence locator.
5. Reject unavailable snippets as support for core facts.

## Iteration

Each round handles the most consequential gap and preserves three query duties: authority, mechanism, and counterevidence. At the end of every round, write 2–4 Insights with unique IDs plus the input query/source IDs, conflicts, candidate gaps, five gap metrics, and new claim IDs.

Run `insight_gate.py validate-round` after writing each round. A failed gate blocks further searching and writing.

Before Round N where N > 1, run `insight_gate.py prepare-next`. It emits the previous round's complete Insight snapshot to the current search Agent and writes a packet plus a hashed delivery receipt. Include the packet as background for agentic providers. For atomic providers, the host Agent reads it before selecting queries; do not contaminate search keywords merely to prove usage.

Insights must be seen and traceable but are not search commands. Every added-round query records the receipt's Context ID and one state:

```text
used | considered-not-used | countered | background-only
```

All four states pass. The search Agent may follow, ignore, challenge, or retain an Insight as background when another research reason is stronger.

Continue while any important metric remains unresolved. Stop after all required dimensions are covered and one complete round adds no high-value claim.

## Writing and Audit

Run `insight_gate.py validate-run` before writing. It must confirm contiguous Insight rounds, 2–4 Insights per round, one valid receipt for every added round, and the receipt Context ID on every query in that round. It does not check whether queries obey Insights.

Build an unordered argument-evidence map. Let the writer selected in `writing-selection.json` choose narrative structure and titles. Insights may remain available as research memory, but they are not evidence and need not be cited, paraphrased, or used in the report. Then audit all falsifiable statements against source context and repair unsupported language. GLM-5.2 may be selected as the writer and is also the configured OpenRouter independent-audit model for a separate fresh audit call.

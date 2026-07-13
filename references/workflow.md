# Workflow

## Initialization

1. Check provider status with `python3 scripts/configure.py --status --json`.
2. Explicitly ask which optional providers to activate for this run: all, any combination of Exa/Perplexity/Grok Build/KimiCode, or none. Warn that selecting an unconfigured tool makes that provider call fail.
3. Write the answer to `<run-dir>/tool-selection.json` with `scripts/select_tools.py`. Stop and offer setup if a selected provider is unavailable.
4. Show the required OpenRouter service-region notice, then explicitly ask whether the current Agent or one configured OpenRouter model should write the report.
5. Write the answer to `<run-dir>/writing-selection.json` with `scripts/select_writer.py`. An OpenRouter choice without a configured key fails; do not silently substitute another model.
6. Create the remaining ten run artifacts.
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

Log exact queries, provider, time, result count, source IDs, and intent.

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

Each round handles the most consequential gap and preserves three query duties: authority, mechanism, and counterevidence. Update the five gap metrics and new claim IDs.

Continue while any important metric remains unresolved. Stop after all required dimensions are covered and one complete round adds no high-value claim.

## Writing and Audit

Build an unordered argument-evidence map. Let the writer selected in `writing-selection.json` choose narrative structure and titles. Then audit all falsifiable statements against source context and repair unsupported language. GLM-5.2 may be selected as the writer and is also the configured OpenRouter independent-audit model for a separate fresh audit call.

---
name: local-deep-research-perplexity-magazine-style
description: Use for fast, multi-source web research and readable Chinese popular-science magazine writing modeled on Perplexity Deep Research. Separates search and writing agents; supports optional Exa, Perplexity, Grok Build, and KimiCode coverage plus host-native or OpenRouter writing. Explain missing setup and explicitly ask which research providers and final-report writer to activate for every run.
metadata:
  version: "0.4.1"
  license: "MIT"
---

# Local-Deep-Research-Perplexity-Magazine-style

## First Use And Every Research Run

Before planning research, resolve the directory containing this `SKILL.md` as `<skill-dir>`, then run:

```bash
python3 <skill-dir>/scripts/configure.py --status --json
```

### Mandatory welcome

On first use, or whenever provider setup is incomplete, begin with a concise welcome that includes all of the following before asking configuration or routing questions:

> 欢迎使用 Local-Deep-Research-Perplexity-Magazine-style。本 Skill 通过多元搜索工具复现 Perplexity 网页端 Deep Research 的调研节奏，并将搜索 Agent 与写作 Agent 分离，面向较快速、通俗易读的科普杂志文章生产。本 Skill 会先请你选择本轮搜索工具和最终报告写作模型。
>
> 如果你使用的 Agent 原生不支持网络搜索，或者搜索效果较差，建议务必配置完 Exa API 后再开始调研。Exa 提供免费搜索额度，当前官方免费层最高为每月 20,000 次请求，因此强烈推荐启用。额度与规则可能调整，请以官网当期说明为准。若使用原装 Codex，或会员订阅版 Claude Code 且其网络搜索已能满足任务需要，可以不配置 Exa。
>
> Exa 官网：https://exa.ai/  
> 注册与控制台：https://dashboard.exa.ai/  
> API Key 创建入口：https://dashboard.exa.ai/api-keys
>
> Perplexity API 为付费服务，推荐在需要快速综合检索或补齐系统性缺口时进一步配置。若本机已经安装 Kimi CLI 或 Grok Build，也建议启用并告知执行本 Skill 的 Agent，以便覆盖中国国内信息与海外用户、社交平台及草根视角。
>
> 为获得更自然的阅读体验，推荐配置 OpenRouter API。若当前 Agent 使用 DeepSeek V4 Pro、GLM 或 Claude 等适合中文写作的模型，也可以不配置 OpenRouter，直接选择 Current Agent model 完成写作。

Then tell the user how to configure it:

1. Open the Exa dashboard and register or sign in.
2. Open the API Keys page, create a key, and copy it.
3. Write `EXA_API_KEY=<key>` into the exact `key_file` path returned by the status command. The portable path is `<skill-dir>/config/.env.local`.
4. Never ask the user to paste the key into chat.

Display the resolved `key_file` path in the welcome so the user knows the exact file to edit on that installation. Strongly recommend Exa, but do not claim its free allowance is permanent or prevent the user from continuing without it.

If `configured` is false, or no optional provider is enabled:

1. Explain the provider roles and the effect of leaving each disabled.
2. Ask which providers the user wants to enable. Do not ask the user to paste secrets into chat.
3. Start the terminal setup assistant:

```bash
python3 <skill-dir>/scripts/configure.py
```

The assistant stores secrets only in `config/.env.local` and provider switches in `config/tools.local.json`. Both files are ignored by version control. Users who prefer manual setup can copy `config/.env.example` and `config/tools.example.json` to those paths.

Provider roles:

| Provider | Contribution when enabled | Effect when disabled |
|---|---|---|
| Exa | Semantic search, research papers, long-tail sources, domain/date filtering | Discovery relies on the host search and may miss semantically related or specialized pages |
| Perplexity | Sonar search synthesis and Sonar Deep Research for systematic gap filling | The workflow loses its dedicated macro-research pass and must build the overview from ordinary searches |
| Grok Build | Overseas user experience, grassroots views, communities, social platforms, product reputation, emerging disputes | User and social perspectives may be thinner and more dependent on indexed media |
| KimiCode | Chinese-language sources, domestic policy, markets, platforms, media, industries, creators, and communities | China-specific coverage may be incomplete or overly dependent on global search indexes |

Read [references/tool-configuration.md](references/tool-configuration.md) when configuration is missing or a provider fails.

For every new research request, explicitly ask which optional providers to activate for that run. Do this even when a previous run used the same tools. Present these choices:

- `All custom providers`
- `Exa`
- `Perplexity`
- `Grok Build`
- `KimiCode`
- `None`

Allow the user to combine any of the four individual choices. State in the question that a selected provider must already be configured; otherwise its call will fail during research. Do not begin external searching until the user answers, unless the current request already specifies the exact provider selection.

Ask in the user's language using this structure: `Which optional research providers should be active for this run? Choose All, None, or any combination of Exa, Perplexity, Grok Build, and KimiCode. Selected tools must already be configured; otherwise their calls will fail.`

Create the run directory, then record the choice:

```bash
python3 <skill-dir>/scripts/select_tools.py \
  --select all|none|exa,perplexity,grok_build,kimi_code \
  --output <run-dir>/tool-selection.json
```

Exit code `2` means one or more selected tools are not ready. Tell the user which providers are unavailable and offer `configure.py`; do not silently count failed tools as used. `None` keeps the host web search available and disables all optional providers for that run.

Immediately after the search-tool question, explicitly ask which model should write the final report. Do this for every research run even if an earlier run used the same writer. Present these choices:

- `Current Agent model` (the host agent writes directly; no OpenRouter writing call)
- `OpenRouter GLM-5.2`
- `OpenRouter Claude Opus 4.6`
- `OpenRouter Claude Sonnet 5`
- `OpenRouter Gemini 3.1 Pro Preview`

Before presenting the choices, show this notice verbatim in Chinese:

> 如果用户处于OpenAI Anthropic Google可服务国家范围之外，则Openrouter源中目前配置唯一可用的替代写作模型是GLM-5.2，用户只能选择此模型，或者解除Openrouter账户的限制，又或者自己让AI改写skill，修改后端模型id为其他可用模型。

When that service-region condition is known to apply, or the configured OpenAI/Anthropic/Google routes have returned a provider Terms of Service `403`, offer only `Current Agent model` and `OpenRouter GLM-5.2`. Restore the other choices only after the account restriction is removed or the user changes the configured model IDs.

If the user chooses an OpenRouter model, require a configured `OPENROUTER_API_KEY`. Do not silently replace the selected model. Record the choice before searching:

```bash
python3 <skill-dir>/scripts/select_writer.py \
  --select agent|glm-5.2|opus-4.6|sonnet-5|gemini-3.1-pro-preview \
  --output <run-dir>/writing-selection.json
```

## Boundaries

- Build research evidence from the external web and configured external providers.
- Use local files only for process artifacts. Do not treat the local filesystem or a local knowledge base as research evidence unless the user explicitly supplies a document for analysis.
- Never print, quote, or copy API keys into reports, logs, prompts, or source records.
- Provider-generated research reports are macro sources, not verified evidence. Split their claims and inspect cited pages.
- If an optional provider is disabled, continue with available tools and disclose the resulting coverage limitation.

## Required Artifacts

Create a separate run directory containing:

```text
tool-selection.json
writing-selection.json
brief.md
research-map.md
query-log.md
sources.jsonl
insights.md
evidence-ledger.md
outline.md
report.md
citation-audit.md
run-summary.md
```

Use the schemas in [references/artifacts.md](references/artifacts.md).

## Workflow

Read [references/workflow.md](references/workflow.md) before execution. Do not stop after producing a plan unless the user explicitly asks for planning only.

### 1. Frame the research

Extract the central question, required dimensions, counterarguments, audience, style, date range, languages, provider restrictions, and cost constraints. Split the problem into 4–10 verifiable subquestions.

Build an external-perspective coverage table before searching. Check whether the topic needs:

- primary or authoritative sources;
- professional semantic discovery;
- Chinese domestic information;
- overseas users and grassroots experience;
- social or community discussion;
- competing interpretations and counterevidence.

Use only providers that are enabled in `config/tools.local.json` and active in the current run's `tool-selection.json`.

### 2. Run two initial query packs

Each pack contains three complementary query duties:

1. Primary, official, or authoritative evidence.
2. Relationships, comparisons, mechanisms, or history.
3. Counterarguments, disputes, cases, or current gaps.

When relevant and active, include at least one KimiCode query for Chinese domestic information and at least one Grok Build query for overseas users, grassroots, and social perspectives during these initial packs. Do not reserve them only for fallback. When relevance is uncertain, favor inclusion. Use Exa actively for professional, semantic, specialist, paper, domain-filtered, or long-tail discovery. Use Perplexity Sonar for a cited synthetic pass where relationships or the overall terrain need rapid consolidation.

### 3. Check systematic completeness

After the two packs, evaluate required-question coverage, conceptual coherence, geography/language diversity, user perspectives, source-type diversity, and unresolved conflicts.

If results remain incomplete or fragmented and Perplexity is active, call Sonar Deep Research. This gate is mandatory when the condition is met. Record the call and import its URLs and claims into the candidate pool. Do not mark the generated report itself as read or verified.

If Perplexity is disabled, continue targeted searches and state that the systematic macro pass was unavailable.

### 4. Read sources and track evidence

- Discover 12–18 candidate sources per pack when the topic supports that breadth.
- Deduplicate canonical URLs.
- Treat snippets as `discovered`, never as full evidence.
- Read 3–6 high-value sources per round.
- Prefer primary documents, peer-reviewed work, official institutions, formal publishers, and direct first-person material appropriate to the claim.
- Track `discovered → shortlisted → read → cited → verified`.

### 5. Iterate by gaps

After each round, update Insights, claims, conflicts, source quality, perspective coverage, and the next highest-value gap. Continue while any required dimension, authority, conflict, applicable perspective, or systematic overview remains unresolved.

Stop only when required dimensions are covered, core facts have read evidence, counterarguments are represented, applicable perspectives are covered or disclosed, and a final round adds no claim that changes the report.

### 6. Write from an unordered evidence map

Use `outline.md` as an unordered argument-evidence map. It constrains required points, claim IDs, relationships, and risk boundaries, but not section order, titles, or wording.

The writing agent chooses the narrative order, merges or splits units, and creates titles. It must not invent evidence to serve the narrative.

Follow `writing-selection.json`. If `agent` is selected, the current host Agent writes `report.md` directly from the research artifacts. If an OpenRouter model is selected, produce the report through `scripts/production_model_router.py`. OpenRouter is never an automatic paid fallback. Read [references/model-routing.md](references/model-routing.md) before routing.

Unless the user explicitly supplies a writing style, every backend must apply this fixed requirement: write idiomatic Chinese in a non-academic, newspaper or general-interest humanities magazine voice; favor flowing narrative over lists; keep icons rare; develop the material as fully as useful without a word limit.

### 7. Audit independently

Scan every number, date, quotation, identity, attribution, causal statement, mechanism, and evidence-dependent recommendation. Classify evidence as `direct`, `synthesis`, or `editorial`, and support status as `supported`, `partially_supported`, `unsupported`, or `source_unavailable`.

Repair misleading or unsupported claims by targeted search, weaker wording, explicit inference labels, or deletion. See [references/quality-rubric.md](references/quality-rubric.md).

GLM-5.2 is also the configured OpenRouter independent-audit model. When an external independent audit is requested, run it as a fresh `--task audit` call after `report.md` exists and save the result separately from the report. If GLM-5.2 also wrote the report, disclose that the audit is process-independent but not model-diverse.

## Tool Selection

Load both the persistent configuration and current run selection rather than assuming a command or MCP exists:

- Host web search: fast background and initial source discovery.
- Exa: semantic and specialist discovery.
- Perplexity Sonar: cited search synthesis.
- Perplexity Sonar Deep Research: mandatory macro pass when initial results are incomplete and the provider is active.
- Web reader available in the host: full-text retrieval from selected URLs.
- KimiCode: Chinese domestic information when relevant and active.
- Grok Build: overseas user, grassroots, community, and social perspectives when relevant and active.

Provider absence must reduce coverage honestly, not silently change a disabled provider to enabled.

Use the bundled runner for optional providers when the host has no equivalent native tool:

```bash
python3 <skill-dir>/scripts/research_tools.py exa-search "<query>" --selection <run-dir>/tool-selection.json
python3 <skill-dir>/scripts/research_tools.py sonar "<query>" --selection <run-dir>/tool-selection.json
python3 <skill-dir>/scripts/research_tools.py deep-submit "<query>" --selection <run-dir>/tool-selection.json
python3 <skill-dir>/scripts/research_tools.py grok-search "<query>" --selection <run-dir>/tool-selection.json
python3 <skill-dir>/scripts/research_tools.py kimi-search "<query>" --selection <run-dir>/tool-selection.json
```

See [references/tool-configuration.md](references/tool-configuration.md) for complete commands, readiness rules, and Deep Research polling.

## Completion

The task is complete only when `report.md`, `evidence-ledger.md`, `citation-audit.md`, and `run-summary.md` exist, core claims are traceable, provider usage is recorded, and remaining coverage limits are disclosed.

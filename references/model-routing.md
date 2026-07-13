# Production Model Routing And Audit

The router produces `report.md` or a separate independent audit from completed research artifacts. It does not replace searching or evidence tracking.

## Backends

- `agent` is the default: the current host Agent writes directly in the active session.
- `openrouter` is an explicit paid option using the OpenAI-compatible Chat Completions endpoint at `https://openrouter.ai/api/v1/chat/completions`.
- Paid backends never activate automatically and there is no automatic paid fallback.

At the beginning of every research run, before searching, ask the user to select the final-report writer. Record the answer in `writing-selection.json`; never infer it from a previous run.

Show this notice before the choices:

> 如果用户处于OpenAI Anthropic Google可服务国家范围之外，则Openrouter源中目前配置唯一可用的替代写作模型是GLM-5.2，用户只能选择此模型，或者解除Openrouter账户的限制，又或者自己让AI改写skill，修改后端模型id为其他可用模型。

If this condition applies, or OpenAI/Anthropic/Google routes return a provider Terms of Service `403`, the active choices are limited to the current Agent and GLM-5.2. Do not attempt the restricted models again until the account restriction is removed or the configured model IDs change.

OpenRouter model choices:

| Choice | OpenRouter model ID |
|---|---|
| `glm-5.2` | `z-ai/glm-5.2` |
| `opus-4.6` | `anthropic/claude-opus-4.6` |
| `sonnet-5` | `anthropic/claude-sonnet-5` |
| `gemini-3.1-pro-preview` | `google/gemini-3.1-pro-preview` |

The router applies no monetary budget ceiling. A smoke test uses `max_tokens=256` so reasoning models can still return a short final answer; normal report generation does not send a local output-token cap.

## Credentials

Set `OPENROUTER_API_KEY` in `config/.env.local` or in the process environment. The status and smoke commands never print the key.

```bash
python3 scripts/production_model_router.py check --backend openrouter --model-choice glm-5.2
python3 scripts/production_model_router.py smoke --backend openrouter --model-choice glm-5.2
```

## Context Packaging

OpenRouter Chat Completions cannot read local files. Before sending the writing request, the router packages these existing run artifacts into the user message:

```text
brief.md
research-map.md
insights.md
evidence-ledger.md
outline.md
sources.jsonl
```

It never imports an existing `report.md`. The writing instruction reiterates that `outline.md` is an unordered claim-evidence map, not a fixed table of contents.

## Report Generation

```bash
python3 scripts/production_model_router.py run \
  --backend openrouter \
  --model-choice sonnet-5 \
  --cwd <run-dir> \
  --prompt-file <run-dir>/writer-prompt.md \
  --output <run-dir>/report.md
```

Use `--style-mode explicit` only when the user explicitly sets a writing style. Otherwise the router injects the skill's default Chinese magazine-style writing contract.

## Independent Audit

GLM-5.2 has two configured roles: `report_writing` and `independent_audit`. Other OpenRouter models are writing-only. Run the audit as a fresh API request after `report.md` exists:

```bash
python3 scripts/production_model_router.py run \
  --backend openrouter \
  --model-choice glm-5.2 \
  --task audit \
  --cwd <run-dir> \
  --prompt-file <run-dir>/audit-prompt.md \
  --output <run-dir>/independent-audit.md
```

The audit request receives `brief.md`, `evidence-ledger.md`, `sources.jsonl`, and `report.md`. It uses an audit contract instead of the magazine-style writing prompt. When GLM-5.2 wrote the report too, describe the audit as process-independent rather than model-diverse.

# Optional Provider Configuration

All optional providers are disabled by default. Run `python3 <skill-dir>/scripts/configure.py`, where `<skill-dir>` contains `SKILL.md`, or configure manually.

## Files

- API keys: `config/.env.local`
- Provider switches and commands: `config/tools.local.json`
- Per-run activation: `<run-dir>/tool-selection.json`
- Safe templates: `config/.env.example` and `config/tools.example.json`

Never commit `.env.local`, `tools.local.json`, CLI credential stores, or copied access tokens.

Persistent setup and per-run activation are separate. A provider is callable only when it is configured, persistently enabled, and selected for the current run. At the start of every research request, ask the user to choose all providers, any combination of the four providers, or none. Warn that an unconfigured selection fails rather than silently falling back.

```bash
python3 scripts/select_tools.py --output <run-dir>/tool-selection.json
python3 scripts/select_tools.py --select all --output <run-dir>/tool-selection.json
python3 scripts/select_tools.py --select exa,grok_build --output <run-dir>/tool-selection.json
python3 scripts/select_tools.py --select none --output <run-dir>/tool-selection.json
```

## Exa

Enable for semantic discovery, papers, and specialist sources. If the host Agent has no native web search or its search quality is weak, configure Exa before starting research. Exa is strongly recommended because it provides a free search allowance; its current official pricing page advertises up to 20,000 free requests per month, subject to change.

- Website: `https://exa.ai/`
- Registration/dashboard: `https://dashboard.exa.ai/`
- API Key page: `https://dashboard.exa.ai/api-keys`

Register or sign in, open the API Key page, create a key, and place it in the installation's `config/.env.local`. The status command prints that file's resolved path.

Put the key in:

```dotenv
EXA_API_KEY=
```

The setup assistant writes this field using a hidden terminal prompt.

```bash
python3 scripts/research_tools.py exa-search "<query>" \
  --selection <run-dir>/tool-selection.json --num-results 10
```

## Perplexity

Enable for Sonar search and Sonar Deep Research.

Put the key in:

```dotenv
PERPLEXITY_API_KEY=
```

When disabled, the systematic-gap gate falls back to ordinary targeted searches.

```bash
python3 scripts/research_tools.py sonar "<query>" \
  --selection <run-dir>/tool-selection.json --model sonar-pro --context high
python3 scripts/research_tools.py deep-submit "<query>" \
  --selection <run-dir>/tool-selection.json --output <run-dir>/deep-submit.json
python3 scripts/research_tools.py deep-wait "<job-id>" \
  --selection <run-dir>/tool-selection.json --output <run-dir>/deep-result.json
```

Use Sonar for cited synthesis. When the first two query packs remain incomplete or fragmented, call Sonar Deep Research if Perplexity is active.

## Grok Build

Install the `grok` command, then authenticate with one of:

```bash
grok login
grok login --device-auth
```

For API-key authentication, put the key in `config/.env.local`:

```dotenv
XAI_API_KEY=
```

The provider command is configured in `config/tools.local.json`, defaulting to `grok` without a machine-specific path.

```bash
python3 scripts/research_tools.py grok-search "<query>" \
  --selection <run-dir>/tool-selection.json --output <run-dir>/grok-result.txt
```

Use Grok Build actively when the topic needs overseas users, grassroots views, communities, social platforms, product reputation, or emerging disputes. Community material normally supports viewpoints, not core factual claims.

The runner uses an isolated temporary working directory by default so local files do not enter the research context. Pass `--cwd` only when the user explicitly supplies local material for analysis.

## KimiCode

Install the `kimi` command. The standard CLI login flow is:

```bash
kimi login
kimi doctor config
```

For a custom API/provider adapter, put its key in `config/.env.local`:

```dotenv
KIMI_API_KEY=
```

The provider command defaults to `kimi`. Custom provider details remain in the user's own KimiCode configuration rather than this public skill.

```bash
python3 scripts/research_tools.py kimi-search "<query>" \
  --selection <run-dir>/tool-selection.json --output <run-dir>/kimi-result.txt
```

Use KimiCode actively when the topic needs Chinese domestic policy, markets, platforms, media, industries, creators, or communities. Verify important claims against original sources.

The runner uses the same isolated-working-directory rule for KimiCode.

## OpenRouter Writing Backend

OpenRouter is a report-writing backend, not a search provider, so it is not part of the per-run search-tool selection. Put its key in:

```dotenv
OPENROUTER_API_KEY=
```

The router also accepts the process environment. Check readiness without exposing the key:

```bash
python3 scripts/production_model_router.py check --backend openrouter
```

See [model-routing.md](model-routing.md) for model choices, context packaging, and report generation.

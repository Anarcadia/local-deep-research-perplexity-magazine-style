# Agent 自适应部署指南、可裁剪代码模板与实战避坑录（Adaptation, Templates & Pitfalls）

> **🤖 给正在阅读本文件的对方 AI Agent 的说明**：
> 本文件提供的是**启发式部署指南与可自由裁剪的参考代码模板**，而非要求你死板照搬的硬性规定。
> 每个用户的电脑环境、网关端口、上游渠道命名（Provider Prefixes）与已安装的 CLI 工具都不一样。请你**先探测你主人电脑的真实环境，把下方的配置值和脚本作为参考骨架，替换为你主人电脑上的真实参数**（或者在宿主原生支持空白 Subagent 时，直接用更轻量的原生方式实现）。

---

## 一、 核心架构拆解：如何把「调研」与「撰写」分开并分配模型？

### 1. 阶段划分原则
整套系统在物理上拆为两个阶段：
- **阶段一（调研与提纯，Stage 1）**：由当前主会话模型（调研模型）执行。负责：
  1. 在开场通过 `AskUserQuestion` 与用户厘清课题边界、确认工作模式（Fast / Full）并指定撰写模型；
  2. 调用多元搜索工具与网页正文抓取工具完成信息采集；
  3. 剔除所有搜索过程杂音，生成结构标准的 `<run-dir>/writer-packet.md`（干净写作资料包）。
- **阶段二（独立干净上下文撰写，Stage 2）**：由专职撰写模型在**全新的、极短且零搜索噪音的独立上下文**中执行。它只接收标准杂志主笔 System Prompt 与 `<run-dir>/writer-packet.md`，输出 `<run-dir>/report.md`。

### 2. 模型分配原则（调研模型 vs 撰写模型）
- **调研模型（Research Model）**：**不限模型**。主会话当前正在使用的任何具备工具调用与阅读理解能力的模型均可直接担任。
- **撰写模型（Writer Model）**：**优先使用公认中文叙事与杂志写作质感最好的几个模型**。在正常标准状态下，开场提问应引导用户从以下几类文笔优等生模型（外加跟随主进程兜底项）中指定。
  - *注：以下预设键与匹配关键词为启发式推荐，你在部署时应根据用户环境实际探测到的模型列表进行调整：*
  1. **`Claude Opus 5.5 / 4.5`**（语义关键词示例：`opus-5.5`, `opus-5-5`, `opus-4.5`, `opus-4-5`, `claude-opus`）
  2. **`Claude Sonnet 5.5`**（语义关键词示例：`sonnet-5.5`, `sonnet-5-5`, `claude-sonnet-5`）
  3. **`Gemini 4 Argon`（或同级 Gemini Pro 旗舰模型）**（语义关键词示例：MaGpie 路由组 `group/argon`, `gemini-4-argon`, `argon`, `gemini-3.1-pro`）
  4. **`Gemini 3.7 / 3.8 Flash`**（语义关键词示例：`gemini-3.8-flash`, `gemini-3.7-flash`, `group/gemini`）
  5. **`跟随当前主进程模型`（`follow-main`）**：在免问快速状态、问答超时或用户要求“不要问直接写”时默认启用，沿用当前主会话模型 ID 在独立干净上下文中撰写。

---

## 二、 路由机制详解：如何检测并适配「有 MaGpie」与「无 MaGpie」环境？

### 1. 第一步：运行环境自动探测
当你在帮用户部署本 Skill 时，先在终端运行以下非侵入式探测命令：

```bash
# 1. 检查环境变量中是否已声明本地网关地址（如 MaGpie / LiteLLM / OneAPI）或外部 API Key
python3 -c '
import os
for k in ["MAGPIE_BASE_URL", "ANTHROPIC_BASE_URL", "OPENAI_BASE_URL", "OPENROUTER_API_KEY", "PERPLEXITY_API_KEY", "SERPER_API_KEY", "BOCHA_API_KEY", "METASO_API_KEY", "EXA_API_KEY", "TAVILY_API_KEY"]:
    val = os.environ.get(k, "")
    if "URL" in k:
        print(f"{k}: {val or \"(not set)\"}")
    else:
        print(f"{k}: {\"present\" if val else \"missing\"}")
'

# 2. 探测本地 MaGpie 默认端口（常见为 127.0.0.1:3425，若上方 ANTHROPIC_BASE_URL 为其他本地端口则探测对应端口）
curl -s -m 1 "${ANTHROPIC_BASE_URL:-http://127.0.0.1:3425}/v1/models" | head -c 500 || echo "NO_LOCAL_MAGPIE_ON_DEFAULT_PORT"
```

---

### 2. 场景 A：用户电脑「有 MaGpie 环境」（或类似本地多模型路由网关）

#### MaGpie 路由是怎么工作的？
- **统一本地入口**：MaGpie 在本地监听端口（通常默认为 `http://127.0.0.1:3425`，具体以用户配置为准），将用户自己的多个上游模型渠道（格式通常为 `<your-provider>/<model-id>`）以及智能负载均衡路由组（格式通常为 `group/<group-name>`，如 `group/argon`、`group/gemini`）聚合在同一个本地入口下，提供标准的 `/v1/models`、`/v1/messages` 与 `/v1/chat/completions` 接口。
- **为什么要用“动态语义匹配”而不是写死模型 ID？**
  不同用户在 MaGpie 里绑定的上游渠道名称完全不同（例如同样是 `Claude Opus 5.5`，在用户 A 电脑上可能叫 `<provider-a>/anthropic/claude-opus-5.5`，在用户 B 电脑上可能叫 `<provider-b>/claude-opus-5-5` 或 `group/opus`）。
  因此，路由器应当实时请求 `GET {magpie_base_url}/v1/models`，遍历所有在线模型的 `id`、`display_name` 和 `magpie_label`，用**语义关键词模糊匹配**出当前用户电脑上实际可用的模型 ID！
- **部署建议**：
  1. 先调用一次用户的 `/v1/models`，看看你主人 MaGpie 里实际有哪些模型 ID 和 `group/*` 路由组；
  2. 将下方第三节提供的 `model-routing.json` 模板中的 `preferred_exact` 占位列表，替换为你主人电脑上**真实存在的在线模型 ID**，然后连同 `magpie_writer_router.py` 一起写入 `<skill-dir>/`。

---

### 3. 场景 B：用户电脑「没有 MaGpie」，但宿主支持原生子代理（Subagent，如 Claude Code / Cursor）—— 零配置首选！

- **为什么强烈推荐这个方案给无 MaGpie 的用户**：
  - 如果用户没有装 MaGpie，也不想单独去申请或配置额外的 API Key，**完全不需要强行使用 Python 路由脚本**！
  - 在 Claude Code 等拥有 `Agent`（子代理）工具的宿主中，每次调用 `Agent` 工具都会启动一个**全新的、0 历史负担的空白上下文窗口**。
  - 当主会话写好 `<run-dir>/writer-packet.md` 后，直接调用宿主的 `Agent` 工具（若支持 `model` 参数，可根据用户在 Step 1 的选择传入 `"opus"` 或 `"sonnet"`），给子代理下达以下指令：
    > *“你是独立撰写主笔。请仅读取 `<run-dir>/writer-packet.md` 与 `<skill-dir>/references/writer-packet-and-contracts.md` 第二节的《独立撰写模型标准 System Prompt》，不要进行任何搜索或读取其他文件，独立构思叙事主线并将最终成稿写入 `<run-dir>/report.md`。”*
  - 这样既做到了 **零额外配置、零脚本维护**，又 **100% 实现了「调研与撰写两阶段物理隔离」**！

---

### 4. 场景 C：用户电脑「没有 MaGpie」，但希望使用 OpenRouter / DeepSeek / 硅基流动 / OneAPI 等单 Key 网关

- **工作原理**：下方第三节的 `magpie_writer_router.py` 模板同时内置了标准 OpenAI 兼容协议（`/chat/completions`）分支。
- **部署建议**：
  引导用户在 `<skill-dir>/config/.env.local` 中配置：
  ```dotenv
  WRITER_API_BASE=https://openrouter.ai/api/v1   # 或用户实际使用的兼容网关地址
  WRITER_API_KEY=<用户的_API_KEY>
  ```
  并将 `model-routing.json` 中的模型 ID 调整为该网关支持的模型名（如 `anthropic/claude-opus-4.5`、`anthropic/claude-sonnet-5`、`google/gemini-3.1-pro-preview` 等）。

---

### 5. 场景 D：纯 CLI 终端无状态调用（无 Subagent 工具，无外部 API Key）

- 若在纯 CLI 环境，可直接通过宿主 CLI 的无状态非交互命令把 `writer-packet.md` 喂给独立子进程：
  - Claude CLI：`claude --print --no-session-persistence --tools="" < combined_writer_prompt.md > <run-dir>/report.md`
  - Codex CLI：`codex exec --ephemeral --sandbox read-only --output-last-message <run-dir>/report.md - < combined_writer_prompt.md`

---

## 三、 可裁剪参考代码模板（Reference Templates）

> **提示**：以下 JSON 与 Python 脚本为参考模板。部署时请将 `<your-provider>/...` 等示例占位符替换为你从用户环境中实际探测到的模型 ID，或根据用户的实际环境自由修改。

### 模板 1：`<skill-dir>/config/model-routing.json`（启发式配置模板）

```json
{
  "magpie_base_url": "http://127.0.0.1:3425",
  "fallback_openai_base_url": "https://openrouter.ai/api/v1",
  "default_selection_mode": "follow-main",
  "default_writing_style": "务必使用地道中文，报刊杂志、非学术、大众人文杂志，讲述型的写法去撰写报告，语言自然流动、避免列表清单，图表需要控制出现频率，写作根据内容可以尽可能详细展现，字数不限制。",
  "default_language_conventions": "使用规范的全角中文标点，不使用半角英文逗号、冒号或引号代替中文标点；标题和正文都应符合正式中文出版物的排版习惯。",
  "composition_contract": "除非用户明确指定文章结构，输入的「无序论点—证据地图」仅是无序的论点与证据集合，绝不是文章目录。不要沿用其行顺序、单元标签或研究素材措辞作为章节顺序、标题和固定表达。请先独立判断中心问题与最佳叙事主线，自主重排、合并或拆分论述单元，并拟定更适合成稿的总标题和小标题；同时覆盖全部必选论点，严格遵守证据池与事实禁区的边界，不得虚构未在资料包中提供的事实或数字。",
  "presets": {
    "opus-5.5": {
      "label": "Claude Opus 5.5 / 4.5",
      "description": "旗舰深度叙事主笔，适合人文厚度与复杂逻辑长文",
      "preferred_exact": [
        "group/opus",
        "anthropic/claude-opus-5.5",
        "anthropic/claude-opus-4.5"
      ],
      "semantic_keywords": [
        "opus-5.5",
        "opus-5-5",
        "opus-4.5",
        "opus-4-5",
        "claude-opus"
      ],
      "env_fallback_var": "ANTHROPIC_DEFAULT_OPUS_MODEL"
    },
    "sonnet-5.5": {
      "label": "Claude Sonnet 5.5",
      "description": "均衡流畅，逻辑与杂志叙事兼备",
      "preferred_exact": [
        "group/sonnet",
        "anthropic/claude-sonnet-5.5",
        "anthropic/claude-sonnet-5"
      ],
      "semantic_keywords": [
        "sonnet-5.5",
        "sonnet-5-5",
        "claude-sonnet-5"
      ],
      "env_fallback_var": "ANTHROPIC_DEFAULT_SONNET_MODEL"
    },
    "gemini-4-argon": {
      "label": "Gemini 4 Argon / Pro",
      "description": "极强跨语境综合与长文结构感（优先匹配 Argon 或 Gemini Pro 路由组）",
      "preferred_exact": [
        "group/argon",
        "google/gemini-4-argon",
        "google/gemini-3.1-pro-preview"
      ],
      "semantic_keywords": [
        "group/argon",
        "gemini-4-argon",
        "argon",
        "gemini-3.1-pro"
      ],
      "env_fallback_var": null
    },
    "gemini-3.8-flash": {
      "label": "Gemini 3.7 / 3.8 Flash",
      "description": "高速成稿、轻快通透的日常办公杂志报告主笔",
      "preferred_exact": [
        "group/gemini",
        "google/gemini-3.8-flash",
        "google/gemini-3.7-flash"
      ],
      "semantic_keywords": [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "group/gemini",
        "gemini-flash"
      ],
      "env_fallback_var": null
    },
    "follow-main": {
      "label": "跟随当前主进程模型",
      "description": "默认快速状态或免问状态：直接使用当前主会话的模型 ID 进行独立干净上下文撰写"
    }
  }
}
```

---

### 模板 2：`<skill-dir>/scripts/magpie_writer_router.py`（自适应干净上下文撰写路由器模板）

```python
#!/usr/bin/env python3
"""
Clean-Context Writer Router (Reference Template)

核心职责：
1. 将「调研阶段」与「撰写阶段」严格物理隔离：只接收主会话提纯后的干净写作资料包 (`writer-packet.md`)，
   在全新的、极短且零搜索噪音的独立上下文中调用撰写模型生成 `report.md`。
2. 自适应网关探测：
   - 优先连接本地 MaGpie 或兼容本地路由网关 (`{magpie_base_url}/v1/messages`)；
   - 若本地网关未运行，自动回退读取 `config/.env.local` 或环境变量中的 `WRITER_API_BASE` / `OPENROUTER_API_KEY` 走标准 `/chat/completions`。
3. 支持动态语义模型匹配与 `follow-main` 主进程模型跟随。
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config" / "model-routing.json"
ENV_LOCAL_PATH = SKILL_ROOT / "config" / ".env.local"

REQUIRED_PACKET_SECTIONS = ["写作任务", "无序论点", "证据"]


def load_local_env() -> None:
    if ENV_LOCAL_PATH.exists():
        for raw in ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_config() -> Dict[str, Any]:
    load_local_env()
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def detect_gateway(config: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, Any]]]:
    """探测可用网关，返回 (mode: 'magpie'|'openai_compat', base_url, online_models)。"""
    magpie_url = (
        os.environ.get("MAGPIE_BASE_URL")
        or os.environ.get("ANTHROPIC_BASE_URL")
        or config.get("magpie_base_url", "http://127.0.0.1:3425")
    )
    try:
        r = requests.get(f"{magpie_url.rstrip('/')}/v1/models", timeout=2)
        if r.status_code == 200:
            models = r.json().get("data", [])
            if isinstance(models, list) and models:
                return "magpie", magpie_url.rstrip("/"), models
    except Exception:
        pass

    compat_base = os.environ.get("WRITER_API_BASE") or config.get("fallback_openai_base_url", "https://openrouter.ai/api/v1")
    compat_key = os.environ.get("WRITER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    models = []
    if compat_key:
        try:
            r = requests.get(
                f"{compat_base.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {compat_key}"},
                timeout=5,
            )
            if r.status_code == 200:
                models = r.json().get("data", [])
        except Exception:
            pass
    return "openai_compat", compat_base.rstrip("/"), models


def detect_main_process_model(
    explicit_main_model: Optional[str] = None,
    online_models: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    if explicit_main_model and explicit_main_model.strip():
        return explicit_main_model.strip(), "explicit --main-model"
    for env_key in [
        "CLAUDE_SESSION_MODEL",
        "ANTHROPIC_MODEL",
        "OPENAI_MODEL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
    ]:
        val = os.environ.get(env_key, "").strip()
        if val:
            return val, f"env:{env_key}"
    caps = os.environ.get("CLAUDE_CODE_MODEL_CAPABILITIES", "")
    if caps:
        first_entry = caps.split(";")[0].split("=")[0].strip()
        if first_entry:
            return first_entry, "env:CLAUDE_CODE_MODEL_CAPABILITIES"
    if online_models:
        first_online = online_models[0].get("id", "")
        if first_online:
            return first_online, "online_models[0]"
    return "current-agent-model", "fallback:placeholder"


def resolve_semantic_preset(
    preset_key: str,
    config: Dict[str, Any],
    online_models: List[Dict[str, Any]],
    explicit_main_model: Optional[str] = None,
) -> Dict[str, Any]:
    presets = config["presets"]
    alias_map = {
        "claude-opus-5.5": "opus-5.5",
        "claude-opus-4.5": "opus-5.5",
        "opus": "opus-5.5",
        "claude-sonnet-5.5": "sonnet-5.5",
        "sonnet": "sonnet-5.5",
        "argon": "gemini-4-argon",
        "gemini-4": "gemini-4-argon",
        "flash": "gemini-3.8-flash",
        "gemini-3.7-flash": "gemini-3.8-flash",
        "gemini-flash": "gemini-3.8-flash",
        "main": "follow-main",
        "default": "follow-main",
    }
    normalized = alias_map.get(preset_key.lower().strip(), preset_key.lower().strip())
    if normalized not in presets:
        # 若传入的不是预设键而是直接的模型 ID 或自定义关键词，直接透传或按关键词搜在线列表
        for m in online_models:
            mid = m.get("id", "")
            if preset_key.lower() in mid.lower():
                return {"preset": "custom-match", "label": preset_key, "resolved_model": mid, "candidates": [mid]}
        return {"preset": "custom-direct", "label": preset_key, "resolved_model": preset_key, "candidates": [preset_key]}

    spec = presets[normalized]
    if normalized == "follow-main":
        model_id, source = detect_main_process_model(explicit_main_model, online_models)
        return {
            "preset": "follow-main",
            "label": spec["label"],
            "resolved_model": model_id,
            "resolution_source": source,
            "candidates": [model_id],
        }

    online_ids = [m.get("id", "") for m in online_models if m.get("id")]
    matched: List[str] = []
    for exact in spec.get("preferred_exact", []):
        if exact in online_ids and exact not in matched:
            matched.append(exact)

    keywords = [k.lower() for k in spec.get("semantic_keywords", [])]
    # 优先匹配 routing group (group/*)
    for m in online_models:
        mid = m.get("id", "")
        haystack = f"{mid} {m.get('display_name', '')} {m.get('magpie_label', '')}".lower()
        if mid.startswith("group/") and any(kw in haystack for kw in keywords) and mid not in matched:
            matched.append(mid)
    for m in online_models:
        mid = m.get("id", "")
        haystack = f"{mid} {m.get('display_name', '')} {m.get('magpie_label', '')}".lower()
        if any(kw in haystack for kw in keywords) and mid not in matched:
            matched.append(mid)

    env_var = spec.get("env_fallback_var")
    if env_var and os.environ.get(env_var):
        env_val = os.environ[env_var].strip()
        if env_val and env_val not in matched:
            matched.append(env_val)

    if not matched and spec.get("preferred_exact"):
        matched.append(spec["preferred_exact"][0])

    return {
        "preset": normalized,
        "label": spec["label"],
        "resolved_model": matched[0] if matched else "",
        "resolution_source": "dynamic semantic match" if online_ids else "static fallback",
        "candidates": matched,
    }


def validate_writer_packet(packet_path: Path) -> Tuple[bool, List[str]]:
    if not packet_path.exists():
        return False, [f"写作资料包不存在: {packet_path}"]
    text = packet_path.read_text(encoding="utf-8").strip()
    issues = []
    if len(text) < 120:
        issues.append("writer-packet.md 内容过短，缺少有效证据与论点地图")
    for keyword in REQUIRED_PACKET_SECTIONS:
        if keyword not in text:
            issues.append(f"writer-packet.md 缺少关键结构模块: 需包含「{keyword}」相关段落")
    return len(issues) == 0, issues


def build_clean_prompts(
    config: Dict[str, Any],
    packet_text: str,
    style_mode: str = "default",
    custom_style: Optional[str] = None,
) -> Tuple[str, str]:
    composition = config["composition_contract"]
    lang_conv = config["default_language_conventions"]
    if style_mode == "explicit" and custom_style:
        style_block = custom_style.strip()
    elif style_mode == "explicit":
        style_block = "请严格按照资料包中「写作任务与读者定位」声明的具体文风与格式要求撰写。"
    else:
        style_block = config["default_writing_style"]

    system_prompt = (
        "你是一位顶级深度杂志主笔。你当前运行在独立的「纯净撰写阶段（Clean-Context Writing Stage）」。\n"
        "你的全部事实依据仅限于下方提供的《Writer Packet（干净写作资料包）》。\n\n"
        f"【文风与排版准则】\n{style_block}\n{lang_conv}\n\n"
        f"【叙事结构与防八股契约】\n{composition}\n\n"
        "【输出要求】\n"
        "直接输出完整的最终成稿 Markdown 正文（包含你独立拟定的总标题、自然流动的章节与必要的来源引用标注），"
        "不要输出任何开场寒暄、自我解释或过程说明。"
    )
    user_message = (
        "请基于以下经过去噪提纯的《Writer Packet（干净写作资料包）》，独立构思叙事主线并完成整篇深度报告撰写：\n\n"
        "=== BEGIN CLEAN WRITER PACKET ===\n"
        f"{packet_text.strip()}\n"
        "=== END CLEAN WRITER PACKET ==="
    )
    return system_prompt, user_message


def call_clean_writer(
    mode: str,
    base_url: str,
    model_id: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 32768,
    timeout: int = 900,
) -> str:
    if mode == "magpie":
        url = f"{base_url}/v1/messages"
        headers = {"anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {
            "model": model_id,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
            "stream": True,
        }
        try:
            r = requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout)
            if r.status_code == 200:
                chunks: List[str] = []
                for raw_line in r.iter_lines(decode_unicode=False):
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str or data_str == "[DONE]":
                        continue
                    try:
                        ev = json.loads(data_str)
                        if ev.get("type") == "content_block_delta":
                            delta = ev.get("delta", {})
                            if delta.get("type") == "text_delta" and delta.get("text"):
                                chunks.append(delta["text"])
                    except Exception:
                        pass
                text = "".join(chunks).strip()
                if text:
                    return text
        except Exception:
            pass

        payload["stream"] = False
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if r.status_code >= 400 and max_tokens > 16384:
            payload["max_tokens"] = 16384
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return "".join(b.get("text", "") for b in data.get("content", []) if isinstance(b, dict)).strip()

    # OpenAI / OpenRouter compatible fallback
    api_key = os.environ.get("WRITER_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "未检测到本地 MaGpie 网关，且未配置 WRITER_API_KEY / OPENROUTER_API_KEY。"
            "请配置 API Key，或直接改用宿主原生空白 Subagent 读取 writer-packet.md 进行撰写。"
        )
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code >= 400 and max_tokens > 16384:
        payload["max_tokens"] = 16384
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def main():
    parser = argparse.ArgumentParser(description="Clean-Context Writer Router")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("--main-model")

    p_val = sub.add_parser("validate-packet")
    p_val.add_argument("--packet", type=Path, required=True)

    p_write = sub.add_parser("write")
    p_write.add_argument("--packet", "--prompt-file", dest="packet", type=Path, required=True)
    p_write.add_argument("--output", type=Path, required=True)
    p_write.add_argument("--preset", "--model-choice", dest="preset", default="follow-main")
    p_write.add_argument("--main-model")
    p_write.add_argument("--model-id")
    p_write.add_argument("--style-mode", choices=["default", "explicit"], default="default")
    p_write.add_argument("--custom-style")
    p_write.add_argument("--max-tokens", type=int, default=32768)

    args = parser.parse_args()
    config = load_config()

    if args.command == "check":
        mode, base_url, models = detect_gateway(config)
        presets_report = {
            k: resolve_semantic_preset(k, config, models, args.main_model) for k in config["presets"]
        }
        print(
            json.dumps(
                {
                    "gateway_mode": mode,
                    "base_url": base_url,
                    "online_model_count": len(models),
                    "presets": presets_report,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "validate-packet":
        ok, issues = validate_writer_packet(args.packet.resolve())
        if not ok:
            print(json.dumps({"valid": False, "issues": issues}, ensure_ascii=False, indent=2), file=sys.stderr)
            raise SystemExit(2)
        print(json.dumps({"valid": True, "packet": str(args.packet.resolve())}, ensure_ascii=False))
    elif args.command == "write":
        packet_path = args.packet.resolve()
        output_path = args.output.resolve()
        ok, issues = validate_writer_packet(packet_path)
        if not ok:
            raise SystemExit(f"writer-packet.md 校验失败: {issues}")
        mode, base_url, models = detect_gateway(config)
        if args.model_id:
            resolved_model = args.model_id.strip()
        else:
            info = resolve_semantic_preset(args.preset, config, models, args.main_model)
            resolved_model = info["resolved_model"]
        sys_prompt, user_msg = build_clean_prompts(
            config, packet_path.read_text(encoding="utf-8"), args.style_mode, args.custom_style
        )
        started = time.time()
        text = call_clean_writer(mode, base_url, resolved_model, sys_prompt, user_msg, args.max_tokens)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "status": "ok",
                    "gateway_mode": mode,
                    "resolved_model": resolved_model,
                    "elapsed_seconds": round(time.time() - started, 2),
                    "output_chars": len(text),
                    "output": str(output_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
```

---

### 模板 3：`<skill-dir>/scripts/insight_gate.py`（模式二重度深研可选门禁参考脚本）

> **软性使用说明**：此脚本仅在用户显式启用 **模式二（Full Mode，学术级重度深研）** 时使用，用于辅助检查每轮是否提炼了 2–4 条 Insight 并生成跨轮上下文回执。如果宿主 Agent 更倾向于直接在会话内按 [references/writer-packet-and-contracts.md](writer-packet-and-contracts.md) 的字段模板维护 `insights.md`，也可将其作为软性结构参考。

```python
#!/usr/bin/env python3
"""Validate mandatory Insights and deliver them to the next search round (Full Mode Optional Gate)."""

from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

ROUND_HEADING = re.compile(r"^##\s+Round\s+R?(\d+)\s*$", re.MULTILINE)
INSIGHT_LINE = re.compile(r"^-\s+Insight\s+(I-R(\d+)-\d{2})[：:]\s*(.+)$", re.MULTILINE)
REQUIRED_FIELDS = (
    "输入查询 IDs", "输入来源 IDs", "新概念", "冲突/不确定性", "候选下一轮缺口",
    "coverage", "authority_gap", "open_conflicts", "perspective_gap",
    "systematic_gap", "high_value_delta", "新增高价值 Claim IDs",
)
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

def field_value(section: str, label: str) -> str:
    match = re.search(rf"^-\s+{re.escape(label)}[：:]\s*(.+)$", section, re.MULTILINE)
    if not match or not match.group(1).strip():
        raise InsightGateError(f"missing or empty field: {label}")
    return match.group(1).strip()

def parse_round(section: str, round_number: int) -> dict:
    insights = []
    for insight_id, id_round, statement in INSIGHT_LINE.findall(section):
        if int(id_round) != round_number:
            raise InsightGateError(f"{insight_id} does not belong to Round {round_number}")
        insights.append({"insight_id": insight_id, "statement": statement.strip()})
    if not 2 <= len(insights) <= 4:
        raise InsightGateError(f"Round {round_number} must contain 2-4 Insights; found {len(insights)}")
    ids = [item["insight_id"] for item in insights]
    if len(ids) != len(set(ids)):
        raise InsightGateError(f"Round {round_number} contains duplicate Insight IDs")
    fields = {label: field_value(section, label) for label in REQUIRED_FIELDS}
    for label in ("输入查询 IDs", "输入来源 IDs"):
        if fields[label].lower() in {"none", "n/a", "无"}:
            raise InsightGateError(f"Round {round_number} requires non-empty {label}")
    return {"round": round_number, "insights": insights, "insight_ids": ids, "fields": fields, "section": section}

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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def write_context_log(run_dir: Path, records: list[dict]) -> None:
    path = run_dir / "insight-context.jsonl"
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")

def prepare_next(run_dir: Path, from_round: int, next_round: int, agent: str) -> tuple[dict, str]:
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
        f"- Context ID: {context_id}\n- From round: {from_round}\n"
        f"- Insight IDs: {', '.join(current['insight_ids'])}\n- Snapshot SHA256: {digest}\n"
        f"- Delivered to: {agent}\n\n{snapshot}\n"
    )
    packet.write_text(content, encoding="utf-8")
    record = {
        "context_id": context_id, "from_round": from_round, "next_round": next_round,
        "insight_ids": current["insight_ids"], "snapshot_sha256": digest,
        "packet_file": str(relative_packet), "delivered_to": agent,
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
    header_index = next((i for i, l in enumerate(lines) if l.strip().startswith("|") and "Round" in l and "Insight Context" in l), None)
    if header_index is None:
        raise InsightGateError("query-log.md is missing Insight context columns")
    headers = [item.strip() for item in lines[header_index].strip().strip("|").split("|")]
    positions = {name: headers.index(name) for name in ("Round", "Query ID", "Insight Context", "Context influence")}
    rounds: dict[int, list[dict]] = {}
    for line in lines[header_index + 2:]:
        if not line.strip().startswith("|"):
            continue
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        match = re.fullmatch(r"R(\d+)", cells[positions["Round"]], re.IGNORECASE)
        if match:
            rounds.setdefault(int(match.group(1)), []).append({
                "query_id": cells[positions["Query ID"]],
                "context_id": cells[positions["Insight Context"]],
                "influence": cells[positions["Context influence"]],
            })
    return rounds

def validate_run(run_dir: Path) -> dict:
    insight_rounds = load_rounds(run_dir)
    expected = list(range(1, max(insight_rounds) + 1))
    if sorted(insight_rounds) != expected:
        raise InsightGateError("Insight rounds must be contiguous and start at Round 1")
    query_rounds = parse_query_log(run_dir)
    records = load_context_log(run_dir)
    for number in expected:
        rows = query_rounds.get(number, [])
        if number == 1:
            if any(row["context_id"] != "initial-brief" for row in rows):
                raise InsightGateError("Round 1 queries must use initial-brief context")
            continue
        matches = [item for item in records if item.get("next_round") == number]
        if len(matches) != 1:
            raise InsightGateError(f"Round {number} requires exactly one context receipt")
        receipt = matches[0]
        for row in rows:
            if row["context_id"] != receipt["context_id"] or row["influence"] not in INFLUENCE_VALUES:
                raise InsightGateError(f"Invalid context reference in Round {number}")
    return {"ok": True, "insight_rounds": len(insight_rounds)}

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    v_round = sub.add_parser("validate-round")
    v_round.add_argument("--run-dir", type=Path, required=True)
    v_round.add_argument("--round", type=int, required=True)
    prep = sub.add_parser("prepare-next")
    prep.add_argument("--run-dir", type=Path, required=True)
    prep.add_argument("--from-round", type=int, required=True)
    prep.add_argument("--next-round", type=int, required=True)
    prep.add_argument("--agent", required=True)
    v_run = sub.add_parser("validate-run")
    v_run.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.expanduser().resolve()
    if args.command == "validate-round":
        res = validate_round(run_dir, args.round)
        print(json.dumps({"ok": True, "round": args.round, "insight_ids": res["insight_ids"]}, ensure_ascii=False))
    elif args.command == "prepare-next":
        rec, content = prepare_next(run_dir, args.from_round, args.next_round, args.agent)
        print(content)
        print(json.dumps(rec, ensure_ascii=False))
    else:
        print(json.dumps(validate_run(run_dir), ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### 模板 4：可选扩展搜索接口参考协议（按用户实际拥有的 Key 选用）

如果用户希望额外部署独立的扩展搜索组件（用于日常搜索兜底、查缺补漏或 Deep Research 多源并发），常见搜索接口的标准请求格式如下（仅供参考，用户有哪些 Key 就接哪些）：

1. **博查搜索（Bocha，`BOCHA_API_KEY`）**：
   - `POST https://api.bochaai.com/v1/web-search`
   - Headers：`{"Authorization": "Bearer <BOCHA_API_KEY>", "Content-Type": "application/json"}`
   - Body：`{"query": query, "freshness": "oneYear", "summary": True, "count": 10}`
   - 解析路径：`resp.json()["data"]["webPages"]["value"]`（每项含 `name`, `url`, `summary`, `siteName`, `datePublished`）。
2. **秘塔搜索（Metaso，`METASO_API_KEY`）**：
   - `POST https://metaso.cn/api/v1/search`
   - Headers：`{"Authorization": "Bearer <METASO_API_KEY>", "Content-Type": "application/json"}`
   - Body：`{"q": query, "scope": "webpage", "includeSummary": True, "size": 10}`
   - 解析路径：`resp.json().get("data", resp.json())["webpages"]`（每项含 `title`, `link`, `summary`, `date`）。
3. **Google Serper（`SERPER_API_KEY`）**：
   - `POST https://google.serper.dev/search`
   - Headers：`{"X-API-KEY": "<SERPER_API_KEY>", "Content-Type": "application/json"}`
   - Body：`{"q": query, "num": 10}`
   - 解析路径：`resp.json()["organic"]`（每项含 `title`, `link`, `snippet`, `date`）。
4. **Perplexity Sonar 系列（`PERPLEXITY_API_KEY`）**：
   - `POST https://api.perplexity.ai/chat/completions`
   - Headers：`{"Authorization": "Bearer <PERPLEXITY_API_KEY>", "Content-Type": "application/json"}`
   - Body：`{"model": "sonar-pro", "messages": [{"role": "user", "content": query}], "return_citations": True}`（模型可选 `sonar` / `sonar-pro` / `sonar-reasoning-pro`）。
5. **免 Key 网页正文读取保底（Jina Reader）**：
   - `GET https://r.jina.ai/<目标URL>`，Headers：`{"Accept": "text/markdown"}`。

---

## 四、 实战避坑总结（Gotchas —— 供 Agent 编写适配代码时参考）

1. **【经验 1】思考链模型（Reasoning Models）的输出 Token 预算**
   - `Claude Opus 5.5`、`Gemini 4 Argon`、`Gemini 3.7/3.8 Flash` 在输出正文前会消耗数千个思考 token。建议将撰写请求的 `max_tokens` 设为较大的安全值（如 **`32768`**，若网关报错超出上限再自动回退 `16384`）。
2. **【经验 2】万字长文生成期间建议使用流式请求（Streaming）**
   - 撰写长文耗时 60–130 秒，HTTP 调用优先开启 **`stream: true`**，防止因空闲超时断开。
3. **【经验 3】禁止全盘递归搜索 `.env`**
   - 检查本机已有 API Key 时，严禁对 `~` 跑无限制递归 `find / glob("**/.env*")`，只检查当前环境变量或已知的常规配置目录。
4. **【经验 4】保持 `writer-packet.md` 的无序论点形态**
   - 论点地图必须保持 `[U-01]`, `[U-02]` 的无序集合形态，禁止预写“第一章、第二章”，把寻找叙事主线的权力完全交给独立撰写模型。

# Agent 现场编程适配指南、参考代码与实战踩坑录（Adaptation & Pitfalls）

> 本文件供对方 AI Agent 在帮其用户主人部署本 Skill 时查阅。内含：
> 1. **有 MaGpie 环境** vs **无 MaGpie 环境** 的判断与具体部署方案；
> 2. 船板在本地 MaGpie 环境下的 **原版 `magpie_writer_router.py` 与 `model-routing.json` 完整参考代码**（可直接复制落地或按主人网关改写）；
> 3. 船板在实战中踩过的 4 个关键大坑与规避方法。

---

## 一、 怎么区分用户「有 MaGpie」还是「没有 MaGpie」，并给出最稳妥的部署方案？

### 1. 自动检测方法（Agent 先跑这一步）

在终端运行以下非侵入式探测命令：

```bash
# 检查环境变量与本地 3425 端口（MaGpie 默认端口）
env | grep -iE "MAGPIE|ANTHROPIC_BASE_URL|OPENAI_BASE_URL" || true
curl -s -m 1 http://127.0.0.1:3425/v1/models | head -c 300 || echo "NO_LOCAL_MAGPIE"
```

- **判定为「有 MaGpie 环境」**：`http://127.0.0.1:3425/v1/models` 返回了包含模型列表的 JSON（通常带有 `magpie_label` 或 `group/` 路由组）。
- **判定为「无 MaGpie 环境」**：连接被拒绝或超时，且环境变量未指向其他本地多模型网关。

---

### 2. 分场景部署策略

#### 场景 A：用户电脑「有 MaGpie」（船板同款满血部署）
- **部署动作**：
  1. 直接将本文件第四节附带的 `model-routing.json` 写入 `<skill-dir>/config/model-routing.json`；
  2. 将第四节附带的 `magpie_writer_router.py` 写入 `<skill-dir>/scripts/magpie_writer_router.py` 并 `chmod +x`；
  3. 运行 `python3 <skill-dir>/scripts/magpie_writer_router.py check` 查看自动语义匹配到的模型 ID（若主人 MaGpie 里的模型名称不同，帮主人微调 `model-routing.json` 里的 `semantic_keywords` 即可）。

#### 场景 B：用户电脑「没有 MaGpie」，但使用的是 Claude Code / Cursor 等支持原生子代理（Subagent）的宿主（最推荐的零配置通用方案！）
- **核心原理**：
  - 很多普通用户既没有装 MaGpie，也不想单独去申请 OpenRouter API Key。
  - 此时千万**不要**退化成“在已经搜了几万字网页的主会话里直接写报告”！
  - 请直接利用宿主自带的 **`Agent`（子代理 / Task）工具**：当主会话完成搜索、读完原文、生成好干净的 `<run-dir>/writer-packet.md` 后，**派生一个全新的空白 Subagent**，只给它传一句指令：
    > *“请读取 `<run-dir>/writer-packet.md` 以及 `<skill-dir>/references/writer-packet-and-contracts.md` 第二节的《独立撰写模型标准 System Prompt》，在完全不启动任何搜索的情况下，基于资料包写出 `<run-dir>/report.md`。”*
- **为什么这完美复刻了船板的核心思路**：
  - 新派生的 Subagent 上下文窗口是 **100% 干净空白** 的，主会话里的搜索残渣半个字都不会漏进去；
  - 零 API 配置成本，直接复用用户主人的现有宿主订阅；
  - 如果宿主的 `Agent` 工具支持 `model` 参数（例如 Claude Code 支持传 `model: "opus"` 或 `"sonnet"`），你依然可以在第一轮询问主人：“撰写阶段你想用 Opus 还是 Sonnet，或者直接跟随当前主模型？”

#### 场景 C：用户电脑「没有 MaGpie」，但配置了 OpenRouter / DeepSeek / 硅基流动 / OneAPI 等兼容网关
- **部署动作**：
  - 直接复用本文件第四节的 `magpie_writer_router.py` 代码骨架，只需把请求地址改为用户的网关地址（如 `https://openrouter.ai/api/v1/chat/completions`），从 `<skill-dir>/config/.env.local` 读取用户的 `API_KEY` 即可！因为该脚本本身就是把 `writer-packet.md` 作为单轮消息发出去，改造成 OpenAI 兼容格式只需调整 10 行 payload 代码。

#### 场景 D：纯 CLI 终端环境（无 Subagent，无外部 API Key）
- **部署动作**：
  - 使用宿主 CLI 的无状态非交互模式实现上下文隔离：
    - Claude CLI：`claude --print --no-session-persistence --tools="" < combined_writer_prompt.md > report.md`
    - Codex CLI：`codex exec --ephemeral --sandbox read-only --output-last-message report.md - < combined_writer_prompt.md`

---

## 二、 搜索与网页全文读取的通用适配方案

1. **搜索源组合（有什么用什么）**：
   - **基础层**：宿主自带的 `WebSearch` 或用户已安装的 `Exa` / `Tavily` MCP。
   - **扩展层（可选）**：如果用户有 `PERPLEXITY_API_KEY`、`SERPER_API_KEY`（Google）、`BOCHA_API_KEY`（博查，`POST https://api.bochaai.com/v1/web-search`）、`METASO_API_KEY`（秘塔，`POST https://metaso.cn/api/v1/search`），你可以帮他生成一两个简单的并发搜索脚本，在需要“多模型扩展搜索 / 查缺补漏”或深研时调用。
2. **网页全文抓取零配置保底（必配！）**：
   - 无论用户有没有配搜索 API，“精读 3–5 篇核心原文正文”都是硬性要求。
   - 如果用户没有装本地 `Firecrawl` 或 `jina-fetch`，直接在 Bash 或 Python 中使用 **免 Key 的 Jina Reader 匿名前缀**：
     ```bash
     curl -fsSL -H "Accept: text/markdown" "https://r.jina.ai/https://example.com/article"
     ```
   - 抓取后检查字数是否大于 300 字且不含 `captcha / access denied / 403`，即可作为高质量原文输入。

---

## 三、 实战踩坑记录（Gotchas —— 必看！）

1. **【大坑 1】带思考链的模型（Reasoning Models）因 `max_tokens` 过小导致文章腰斩**
   - `Claude Opus 5.5`、`Gemini 4 Argon`、`Gemini 3.8 Flash`、`DeepSeek R1/V4` 等模型在生成长文前会消耗数千个 thinking/reasoning tokens，而很多网关把 thinking tokens 也计入 `max_tokens`。
   - **规避规则**：撰写报告的 API 请求，务必将 `max_tokens` 默认设为 **`32768`**（若网关限制上限为 `16384` 则自动回退 `16384`），千万不要设为 `4096`！
2. **【大坑 2】生成万字杂志长文时非流式请求触发 60 秒网关超时**
   - 写一篇 8,000 字的深度杂志文章通常耗时 60–130 秒。
   - **规避规则**：通过 HTTP API 调撰写模型时，**优先开启 `stream: true`（SSE 流式接收）**，边收 chunk 边拼接，避免连接因长时间空闲被掐断。
3. **【大坑 3】全盘递归搜索 `.env` 导致进程卡死**
   - 探测用户电脑上是否存过 API Key 时，**严禁**对 `~` 或大型文档库跑递归 `find / glob("**/.env*")`。只定点检查已知配置目录或 `zsh -ic` 环境变量。
4. **【大坑 4】把 `writer-packet.md` 写成顺序大纲**
   - 只要你在 `writer-packet.md` 里写了“一、二、三、四”的章节顺序，主笔模型就会偷懒变成填空机器。必须保持 `[U-01]`, `[U-02]` 的无序集合形态，强制主笔自己找叙事线。

---

## 四、 船板原版 MaGpie 路由器参考代码（供有 MaGpie 或兼容网关的环境直接复用）

### 1. `config/model-routing.json` 参考配置

```json
{
  "magpie_base_url": "http://127.0.0.1:3425",
  "default_selection_mode": "follow-main",
  "default_writing_style": "务必使用地道中文，报刊杂志、非学术、大众人文杂志，讲述型的写法去撰写报告，语言自然流动、避免列表清单，图表需要控制出现频率，写作根据内容可以尽可能详细展现，字数不限制。",
  "default_language_conventions": "使用规范的全角中文标点，不使用半角英文逗号、冒号或引号代替中文标点；标题和正文都应符合正式中文出版物的排版习惯。",
  "composition_contract": "除非用户明确指定文章结构，输入的「无序论点—证据地图」仅是无序的论点与证据集合，绝不是文章目录。不要沿用其行顺序、单元标签或研究素材措辞作为章节顺序、标题和固定表达。请先独立判断中心问题与最佳叙事主线，自主重排、合并或拆分论述单元，并拟定更适合成稿的总标题和小标题；同时覆盖全部必选论点，严格遵守证据池与事实禁区的边界，不得虚构未在资料包中提供的事实或数字。",
  "presets": {
    "opus-5.5": {
      "label": "Claude Opus 5.5",
      "preferred_exact": ["zenmux/anthropic/claude-opus-5.5", "commandcode/claude-opus-5-5"],
      "semantic_keywords": ["opus-5.5", "opus-5-5", "claude-opus-5"],
      "env_fallback_var": "ANTHROPIC_DEFAULT_OPUS_MODEL"
    },
    "gemini-4-argon": {
      "label": "Gemini 4 Argon",
      "preferred_exact": ["group/argon", "zenmux/google/gemini-4-argon"],
      "semantic_keywords": ["group/argon", "gemini-4-argon", "argon"],
      "env_fallback_var": null
    },
    "gemini-3.8-flash": {
      "label": "Gemini 3.8 Flash",
      "preferred_exact": ["commandcode/google/gemini-3.8-flash", "zenmux/google/gemini-3.8-flash"],
      "semantic_keywords": ["gemini-3.8-flash", "gemini-3-8-flash"],
      "env_fallback_var": null
    },
    "follow-main": {
      "label": "跟随当前主进程模型"
    }
  }
}
```

### 2. `scripts/magpie_writer_router.py` 核心实现参考

```python
#!/usr/bin/env python3
"""MaGpie Clean-Context Writer Router — 物理隔离调研与撰写阶段，支持动态语义选模与主进程模型跟随。"""
import argparse, json, os, sys, time
from pathlib import Path
import requests

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config" / "model-routing.json"
REQUIRED_SECTIONS = ["写作任务", "无序论点", "证据"]

def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def fetch_online_models(base_url):
    try:
        r = requests.get(f"{base_url.rstrip('/')}/v1/models", timeout=5)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception:
        return []

def resolve_preset(preset_key, config, online_models, explicit_main_model=None):
    if preset_key == "follow-main":
        mid = explicit_main_model or os.environ.get("ANTHROPIC_MODEL") or os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or "group/argon"
        return {"preset": "follow-main", "resolved_model": mid}
    spec = config["presets"][preset_key]
    online_ids = [m.get("id", "") for m in online_models if m.get("id")]
    candidates = [e for e in spec.get("preferred_exact", []) if e in online_ids]
    keywords = [k.lower() for k in spec.get("semantic_keywords", [])]
    for m in online_models:
        mid = m.get("id", "")
        hay = f"{mid} {m.get('display_name','')} {m.get('magpie_label','')}".lower()
        if any(k in hay for k in keywords) and mid not in candidates:
            candidates.append(mid)
    if not candidates and spec.get("preferred_exact"):
        candidates.append(spec["preferred_exact"][0])
    return {"preset": preset_key, "resolved_model": candidates[0], "candidates": candidates}

def call_clean_writer(base_url, model_id, system_prompt, user_message, max_tokens=32768):
    url = f"{base_url.rstrip('/')}/v1/messages"
    headers = {"anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['ANTHROPIC_AUTH_TOKEN']}"
    payload = {
        "model": model_id,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
        "stream": True,
    }
    r = requests.post(url, headers=headers, json=payload, stream=True, timeout=900)
    if r.status_code == 200:
        chunks = []
        for raw in r.iter_lines(decode_unicode=False):
            if not raw: continue
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data:"): continue
            data_str = line[5:].strip()
            if not data_str or data_str == "[DONE]": continue
            try:
                ev = json.loads(data_str)
                if ev.get("type") == "content_block_delta":
                    chunks.append(ev.get("delta", {}).get("text", ""))
            except Exception:
                pass
        if chunks:
            return "".join(chunks).strip()
    payload["stream"] = False
    r = requests.post(url, headers=headers, json=payload, timeout=900)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", []) if isinstance(b, dict)).strip()
```

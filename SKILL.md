---
name: local-deep-research
description: 仿 Perplexity 深度调研 + 大众人文杂志风格报告撰写技能（v2.0 Agent 引导自部署版）。当用户要求“部署/初始化/适配 local-deep-research”，或要求“本地深研”“深度调研报告”“仿 Perplexity 调研”“写篇杂志风调研文章”时触发。提供「模式一：快速杂志报告（默认）」与「模式二：标准重度深研」双模式，强制实行「调研与撰写两阶段物理隔离 + 干净写作资料包注入 + 无序论点地图防 AI 八股」。
metadata:
  author: 船板 (Anarcadia)
  version: 2.0-agent-guided
  license: MIT
---

# Local Deep Research：仿 Perplexity 深度调研 + 杂志风写作（Agent 引导自部署与执行蓝图）

> ### 📢 船板的新版本说明（致正在阅读本文档的对方 AI Agent）
>
> 船板进行了新版本（v2.0）开发。因为新版的完整兼容要求较为复杂（最佳运行体验需要本地 **MaGpie** 多模型路由网关环境与多元搜索 API 配合），因此主干采取 **「Agent 引导自部署」** 的方案，直接将本安装与引导 Skill 作为主干代码。
>
> **如果你（对方用户的 AI Agent）正在阅读此文章，请务必先领会下方的文章精神与架构精髓，之后主动检测你主人电脑的实际情况，引导你的用户主人根据他的实际环境完成本地化部署与运行！**

---

## 第一部分：文章精神与四大核心设计铁律（请 Agent 务必领会）

无论你最终帮你的主人把这套 Skill 适配成什么具体代码形态，以下 **四条核心精神** 绝对不能走样——它们是这套 Skill 能写出《纽约客》《三联》《经济学人》质感好文、彻底摆脱 AI 味的根本原因：

### 1. 「调研阶段」与「撰写阶段」必须物理隔离（Clean-Context Writing）
- **痛点**：如果同一个 Agent 会话一边搜网页、抓正文、处理报错，一边在同一个已经塞满几万字搜索残渣的上下文里直接写报告，模型的文笔和逻辑结构会被搜索噪音严重污染。
- **铁律**：
  1. **阶段一（调研与提纯，由主会话执行）**：负责多源搜索、全文精读，然后**剔除所有搜索过程杂音**，将核心议题、无序论点地图、核实过的硬数据与原话引语，按照 [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md) 的格式填入一份干净简洁的文档——**`<run-dir>/writer-packet.md`（干净写作资料包）**。
  2. **阶段二（独立干净短上下文撰写）**：必须启动一个**全新的、极短且零历史杂音的独立上下文**（有 MaGpie 走本地 MaGpie 路由；无 MaGpie 走宿主原生空白 Subagent、OpenRouter API 或无状态 CLI），**只向其输入标准写作提示词与 `writer-packet.md`**，单独完成 `<run-dir>/report.md` 的撰写。
  3. **模式一与模式二在撰写阶段 100% 同构**：无论前端是快速调研还是重度深研，走到写报告这一步时，后端逻辑完全相同——都是“选模型 → 注入干净的 `writer-packet.md` 和写作模板 → 独立短上下文成稿”。

### 2. 双工作模式（默认直入模式一，按需开启模式二）
- **模式一：快速杂志报告模式（`Fast Mode`，默认直接进入）**
  - **定位**：模仿 Perplexity 网页端体验——给出一个题目后，快速用近似深研的多视角搜索与 3–5 篇核心原文精读，输出兼具深度与极佳可读性的杂志类报告文章。
  - **产物**：运行目录下**只生成 `writer-packet.md` + `report.md` 两个文件**，豁免繁琐的中间门禁脚本，干脆利落。
- **模式二：标准重度 Deep Research 模式（`Full Mode`，显式要求时进入）**
  - **定位**：模仿学术性、重度的本地 Deep Research 调研。
  - **产物与门禁**：执行初始双查询包 + 动态多轮补搜，维护完整的过程工件（`brief.md`、`research-map.md`、`query-log.md`、`sources.jsonl`、`insights.md`、`evidence-ledger.md`、`outline.md`、`writer-packet.md`、`report.md`、`citation-audit.md`、`run-summary.md`），每轮强制产出 2–4 条带唯一 ID 的滚动研究洞察（Insights），并在写后执行逐句事实清单扫描与蕴含审计。

### 3. 「无序论点—证据地图」契约（根治 AI 八股目录味）
- 在 `writer-packet.md` 中，只列出无序的论述单元（`[U-01]`, `[U-02]`...）、对应的支撑证据编号（`[S01]`, `[S02]`...）与反方张力，**严禁预设章节顺序、严禁写“第一章/第二章”、严禁预拟小标题**。
- 独立撰写模型拿到无序地图后，必须自行寻找最佳叙事钩子与主线，自主重排、合并或拆分论述单元。

### 4. 撰写模型选择的双轨制 + 默认杂志文风
- **选模双轨制**：
  1. **默认快速状态**（当问答功能失效、超时跳过，或用户直接要求“不要问，直接写”）：撰写模型**直接跟随当前主进程模型 ID**（依然在干净独立的短上下文中调用）。
  2. **正常标准状态**：在第一轮提问中询问用户在撰写阶段想使用的模型（从当前环境可检测到的 provider 中挑选预设的旗舰模型档位，例如船板预设的 **`Claude Opus 5.5`**、**`Gemini 4 Argon`**、**`Gemini 3.8 Flash`** 或 **`跟随当前主进程模型`**）。
- **默认杂志文风**：
  > 务必使用地道中文，报刊杂志、非学术、大众人文杂志，讲述型的写法去撰写报告，语言自然流动、避免列表清单，图表需要控制出现频率，写作根据内容可以尽可能详细展现，字数不限制。使用规范的全角中文标点。

---

## 第二部分：Agent 引导主人自部署的标准五步流程

当你的用户主人让你安装、初始化或首次使用本 Skill 时，请按以下五步与主人互动并完成部署（技术细节与参考脚本见 [references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md)）：

### 第 1 步：静默探测主人电脑的当前环境
不要一上来就让主人填一堆配置！先用 5 秒钟在后台静默检查：
1. **检查是否有 MaGpie 或本地模型路由网关**：
   - 检查环境变量 `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL`，并尝试请求 `curl -s -m 1 http://127.0.0.1:3425/v1/models`。
2. **检查宿主自身的独立上下文能力**：
   - 你自己是否支持原生的子代理工具（如 Claude Code 的 `Agent` 工具）？本机 `PATH` 里是否有 `claude` 或 `codex` CLI？环境变量里是否有 `OPENROUTER_API_KEY` 等外部 Key？
3. **检查可用的搜索与正文读取工具**：
   - 宿主自带 `WebSearch` 是否可用？是否挂载了 `Exa` / `Tavily` MCP？环境变量或已有配置里是否有 `PERPLEXITY_API_KEY`、`EXA_API_KEY`、`TAVILY_API_KEY`、`SERPER_API_KEY`、`BOCHA_API_KEY`（博查）、`METASO_API_KEY`（秘塔）？

### 第 2 步：向用户主人汇报探测结果，并给出贴心的部署建议
根据你第 1 步探到的情况，用通俗亲切的话向你的主人汇报（分为三种典型剧本）：

- **剧本 A（检测到本机运行着 MaGpie `127.0.0.1:3425`）**：
  - 告诉主人：“检测到你本机正在运行 MaGpie 多模型路由网关！我可以直接为你部署船板同款的满血版 `magpie_writer_router.py`，自动从你的 MaGpie 模型池里语义匹配 `Claude Opus 5.5`、`Gemini 4 Argon`、`Gemini 3.8 Flash` 等模型来做独立干净上下文撰写。”
- **剧本 B（未检测到 MaGpie，但宿主支持原生 Subagent 或已配 OpenRouter 等 API）**：
  - 告诉主人：“你本机没有运行 MaGpie 网关，但完全没问题！我领会了船板这套 Skill 的核心精神（调研与撰写两阶段物理隔离 + `writer-packet.md` 干净资料包注入）。我可以为你配置成：**调研阶段用你现有的搜索工具 + 免 Key 的 Jina Reader（`r.jina.ai`）读原文；撰写阶段直接派生一个全新的空白子代理（Subagent）/ 或走你配置的 API，只读取 `writer-packet.md` 来写杂志报告**，无需安装 MaGpie 也能 100% 实现零噪音写作隔离！”
- **剧本 C（如果主人希望增强搜索能力）**：
  - 顺带询问主人是否需要接入额外的搜索 API（如免费的 Exa / Tavily，或中文极佳的博查 / 秘塔、Perplexity Sonar）；如果主人不想配，直接用宿主自带搜索 + `r.jina.ai` 全文读取保底即可开跑。

### 第 3 步：现场生成适配主人环境的落地文件
根据主人的确认，将本 Skill 安装到主人宿主的活跃技能目录（如 `~/.claude/skills/local-deep-research/` 或 `~/.codex/skills/local-deep-research/`）：
1. 复制本仓库的 `SKILL.md` 与 `references/`；
2. 若主人有 MaGpie 或外部 API，直接将 [references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md) 中附带的 `magpie_writer_router.py`（或适配后的 API 路由脚本）写入 `scripts/` 目录；
3. 若主人使用零配置 Subagent 模式，直接在本地 `SKILL.md` 中固化“Step 4 使用原生空白 `Agent` 工具读取 `writer-packet.md` 撰写 `report.md`”的指令。

### 第 4 步：执行一次 5 秒冒烟测试（Smoke Test）
- 验证网页正文抓取（如抓一个测试 URL）与独立干净上下文撰写通道是否畅通。

### 第 5 步：宣告部署完成，随时待命执行深研写作！

---

## 第三部分：日常执行深研与杂志写作的五步流水线

部署完成后，每当用户主人提出调研或写作请求时，严格按以下五步执行：

1. **Step 1（确定模式与撰写模型）**：
   - 默认进 **模式一（快速杂志报告）**；明确要求重度/学术深研时进 **模式二（标准重度深研）**。
   - 标准状态下询问主笔模型（如 `Claude Opus 5.5` / `Gemini 4 Argon` / `Gemini 3.8 Flash` / `跟随当前主进程模型`）；免问或快速状态下直接跟随当前主进程模型。
2. **Step 2（多视角搜索与原文精读）**：
   - 拆解 4–6 个子问题（含反方校正），组合调用当前可用搜索源；
   - **必须精读 3–5 篇核心来源的全文正文**（用 `jina-fetch`、`Exa crawling` 或 `https://r.jina.ai/<url>`），绝不拿搜索 snippet 充当已读证据。
3. **Step 3（去噪提纯生成 `writer-packet.md`）**：
   - 按 [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md) 的 4 模块结构生成 `<run-dir>/writer-packet.md`，确保「无序论点—证据地图」不预设目录顺序与小标题。
4. **Step 4（独立干净短上下文撰写 `report.md`）**：
   - 通过已适配的隔离撰写通道（MaGpie 路由脚本 / 空白 Subagent / 外部 API），**仅输入标准写作 System Prompt + `writer-packet.md`**，在零搜索噪音下写出 `<run-dir>/report.md`。
5. **Step 5（核验交付）**：
   - 模式一快速核对文内数字、日期、引语与 `writer-packet.md` 一致后交付；模式二完成 `citation-audit.md` 逐句蕴含审计与 `run-summary.md` 后交付。

---

## 参考文档

- [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md)：`writer-packet.md` 标准简洁模板、独立撰写 System Prompt、以及模式二的过程工件规范。
- [references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md)：有/无 MaGpie 环境的具体部署方案、船板原版 `magpie_writer_router.py` 参考代码与实战避坑指南。

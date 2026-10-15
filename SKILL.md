---
name: local-deep-research
description: 仿 Perplexity 深度调研 + 大众人文杂志风格长文写作技能（v2.0 Agent 引导自部署版）。当用户要求“安装/部署/初始化 local-deep-research”，或要求“本地深研”“深度调研报告”“仿 Perplexity 调研”“写篇杂志风调研文章”时触发。支持「模式一：快速杂志报告（默认）」与「模式二：标准重度深研」双模式；强制执行「开场课题澄清与选模引导 + 调研与撰写两阶段物理隔离 + writer-packet.md 干净资料包注入 + 无序论点地图防 AI 八股」。
metadata:
  author: 船板 (Anarcadia)
  version: 2.0.0
  license: MIT
---

# Local Deep Research：仿 Perplexity 深度调研 + 杂志风长文写作

> **🤖 致正在阅读本文件的 AI Agent**：
> 本文件与同目录下的 `README.md`、`references/` 构成了本 Skill 的**完整、独立（Standalone）蓝图**。请勿参考任何旧分支或历史版本。
> 请注意：除「调研与撰写两阶段物理隔离」「`writer-packet.md` 无序论点契约」与「开场主动引导」为不可妥协的核心精神外，文档中提及的具体端口号、模型 ID 前缀、脚本形态均为**启发式参考与可替换占位**。请充分发挥你的判断力，根据你主人电脑的实际环境灵活裁剪与实现：
> 1. 如果用户是首次安装或让你部署本 Skill，请执行 **「第一章：Agent 引导自部署协议」**；
> 2. 如果本环境已完成部署、用户提出了具体的调研或写作题目，请直接执行 **「第二章：日常深研与杂志写作标准工作流」**。

---

## 第一章：Agent 引导自部署协议（首次安装与环境自适应）

当用户让你从 GitHub 或本地文件夹安装、初始化、适配本 Skill 时，请扮演一名专业、体贴的架构部署向导，按以下 4 个步骤引导用户完成本地化部署（参考实现模板见 [references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md)）：

### Step 1：后台静默探测用户电脑的当前环境

在向用户提问前，先用非侵入式方式快速探明用户电脑的现状：

1. **探测模型路由与独立上下文环境**：
   - 检查环境变量（如 `ANTHROPIC_BASE_URL`、`OPENAI_BASE_URL`、`MAGPIE_BASE_URL`、`OPENROUTER_API_KEY` 等，**仅检查变量是否存在或指向何处，切勿打印密钥明文**）；
   - 若环境变量指向本地端口，或尝试探测本地常见路由端口（如 MaGpie 默认的 `http://127.0.0.1:3425/v1/models`），查看是否返回在线模型池列表；
   - 检查你（宿主 Agent）自身的能力：是否支持原生派生空白子代理（如 Claude Code 的 `Agent` 工具）？本机 `PATH` 中是否有可用的无状态 CLI（如 `claude` 或 `codex`）？
2. **探测可用的搜索与正文读取工具**：
   - 检查宿主自带 `WebSearch` 或已挂载的搜索 MCP（如 `Exa`、`Tavily`、`Brave` 等）是否可用；
   - 检查已知环境变量或常规配置目录中是否已配置其他搜索 API Key（如 `PERPLEXITY_API_KEY`、`SERPER_API_KEY`、`BOCHA_API_KEY`、`METASO_API_KEY`、`EXA_API_KEY`、`TAVILY_API_KEY` 等——**切勿对用户主目录跑全盘递归文件扫描**）；
   - 检查网页全文读取方式：是否有现成的网页转 Markdown 工具（如 `jina-fetch`、`Firecrawl`、`Exa crawling`），并验证免 Key 的 `https://r.jina.ai/<url>` 是否畅通。

### Step 2：向用户汇报探测结果，并通过提问引导用户确认部署方案

将你探测到的环境情况用通俗清晰的话告诉用户，并使用 `AskUserQuestion`（或结构化提问）引导用户确认以下配置选择：

1. **确认「撰写阶段（Stage 2）」的干净上下文实现方案**：
   - **情况 A（检测到本地运行着 MaGpie 或类似本地多模型路由网关）**：
     - 展示你从该网关 `/v1/models` 探测到的可用写作模型（例如匹配到的 `Claude Opus 5.5/4.5`、`Claude Sonnet 5.5`、`Gemini 4 Argon`、`Gemini 3.7/3.8 Flash` 等具体 ID 或 `group/*` 路由组），询问用户是否直接将这套在线模型写入本地路由配置。
   - **情况 B（未检测到本地 MaGpie 网关）**：
     - 温和地向用户提供适合他电脑的选项：
       - **选项 1（零配置原生空白 Subagent 方案，最省心）**：完全无需安装脚本或配置 API Key，在撰写阶段直接利用宿主原生的 `Agent`（子代理）工具派生全新空白上下文读取 `writer-packet.md` 成稿（若宿主支持切换子代理模型如 `opus` / `sonnet` 也可一并开启）；
       - **选项 2（单 Key 外部网关方案，如 OpenRouter / 硅基流动 / 自建 API）**：引导用户在本地 `config/.env.local` 中填入他惯用的 API 地址与 Key，并询问他偏好的几款主力写作模型 ID；
       - **选项 3（如果用户其实装了 MaGpie 但运行在其他自定义端口或尚未启动，请用户告知端口或启动后再探测）**。
2. **确认「搜索阶段（Stage 1）」的工具组合**：
   - 告知用户当前已就绪的搜索工具与网页正文抓取方式；
   - 询问用户是否需要额外接入他手头已有的其他搜索 API（如博查、秘塔、Serper、Perplexity、Exa 等），或直接以当前可用工具开跑。

### Step 3：根据用户环境裁剪并落地 Skill 文件

根据用户的回答，在用户当前宿主的技能目录（如 `~/.claude/skills/local-deep-research/`、`~/.codex/skills/local-deep-research/` 或工作区技能目录）中生成最终适配好的文件：
- **原则：按需生成，不堆砌无用死代码**。
  - 如果用户采用 **MaGpie 或外部 API 网关方案**：参考 [references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md) 中的代码模板，生成贴合用户实际模型 ID 列表的 `config/model-routing.json` 与 `scripts/magpie_writer_router.py`；
  - 如果用户采用 **零配置原生空白 Subagent 方案**：甚至不需要生成外部网关脚本，直接在落地的 `SKILL.md` 中将 Step 4 固定为调用原生空白 `Agent` 工具即可；
  - 如果用户需要用到 **模式二（标准重度深研）**：可落地 `scripts/insight_gate.py` 辅助校验脚本，或由 Agent 在执行模式二时按契约核验。

### Step 4：执行连通性测试并完成交付

对落地后的「原文抓取」与「独立干净上下文撰写」执行一次轻量冒烟测试，确认畅通后向用户宣告部署完成。

---

## 第二章：日常深研与杂志写作标准工作流（五步执行法）

当用户提出一个调研或写作课题时，严格遵循以下五步执行：

---

### Step 1：开场交互引导 —— 厘清课题、确认模式、指定主笔模型

> **核心要求**：在启动搜索前，必须主动通过 `AskUserQuestion`（或简明对话提问）引导用户厘清方向并指定模型。
> **默认快速直通例外**：仅当用户在指令中已明确指定了方向与模型、或明确表示*“不要问，直接写”*、或当前处于非交互/问答超时状态时，跳过提问，默认采用 **模式一（Fast Mode）+ 用户已点名模型（未点名则跟随当前主进程模型 ID）** 直接进入 Step 2。

在正常标准状态下，开场向用户确认以下三项内容：

1. **厘清调研课题焦点与边界**：
   - 针对用户的题目，主动列出 2–3 个最值得深挖的切入维度或需要界定的边界（例如：*“关于这个课题，你是希望侧重剖析底层的机制原理、行业现实博弈，还是具体人物的一线实践方法？有没有不需要展开的方向？”*），请用户确认或补充。
2. **确认工作模式**：
   - **模式一：快速杂志报告模式（`Fast Mode`，默认推荐）** —— 模仿 Perplexity 网页端体验，快速完成一轮多视角检索与核心原文精读，仅生成 `writer-packet.md` 与 `report.md` 两个文件，快速产出兼具深度与可读性的杂志文章。
   - **模式二：标准重度 Deep Research 模式（`Full Mode`）** —— 本地学术级重度调研，执行多轮动态补搜、维护完整过程工件与滚动研究记忆（Insights），并在写后执行逐句事实清单扫描与蕴含审计。
3. **指定「撰写阶段」的主笔模型**：
   - 说明**调研阶段**由当前模型执行，而**撰写阶段**将在独立干净上下文中交由擅长写作的模型主笔。提供当前环境可用的优质写作模型供用户选择（以下为推荐档位，按本机实际可用列表展示）：
     - **`Claude Opus 5.5 / 4.5`**（深度人文叙事与复杂逻辑首选）
     - **`Claude Sonnet 5.5`**（流畅均衡，结构清晰）
     - **`Gemini 4 Argon`**（或同级 Gemini Pro 旗舰路由组，跨领域综合与长文结构感极强）
     - **`Gemini 3.7 / 3.8 Flash`**（高速成稿，轻快通透）
     - **`跟随当前主进程模型`**（沿用当前主会话模型 ID，在独立干净上下文中撰写）

---

### Step 2：阶段一（上）—— 多元外部调研与核心原文精读（由调研模型执行）

创建本次任务的独立运行目录 `<run-dir>`（例如 `Research/YYYYMMDD-<主题简称>/`）。

#### 1. 问题拆解与外部视角规划
- 将课题拆解为若干个可验证的子问题（建议 4–8 个），覆盖：
  - 权威定义、原始文献或硬核事实数据；
  - 历史演变、内在机制或跨领域比较；
  - 本土实践/行业生态视角，或海外用户体验/草根社区视角；
  - **至少 1 个反方争议、局限性或反直觉校正视角**。
- **外部证据边界**：只面向外部互联网与搜索服务建立研究证据，不把用户本地无关文件当作检索来源（除非用户明确指定分析某份本地文档）。

#### 2. 执行多元搜索与全文精读（按模式分流）

- **若为「模式一：快速杂志报告（Fast Mode）」**：
  1. **并行执行 1 轮多元互补搜索**：组合调用当前环境可用的默认搜索与扩展搜索工具。
  2. **强制精读多篇核心原文正文（建议 3–5 篇）**：
     - 绝不能只凭搜索引擎返回的百字摘要（Snippet）写报告！
     - 从搜索结果中精选最权威、细节最丰富的核心文章，使用当前环境最佳的全文读取方式（如 `jina-fetch`、`Exa crawling`、`Firecrawl` 或免 Key 的 `https://r.jina.ai/<url>`）读取完整正文，提取精确数字、案例细节与精彩原话。
  3. 若发现某个必选维度仍有明显事实空白，可按需追加 1 次定向补搜。

- **若为「模式二：标准重度深研（Full Mode）」**：
  1. **初始化过程工件**（参考模板见 [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md)）：`brief.md`、`research-map.md`、`query-log.md`、`sources.jsonl`、`insights.md`、`evidence-ledger.md`、`outline.md`、`citation-audit.md`、`run-summary.md`。
  2. **执行初始双查询包与多轮动态补搜**：
     - 每轮检索后，精选多篇（建议 3–6 篇）A/B 级权威来源读取全文正文，更新 `sources.jsonl` 与 `evidence-ledger.md`；
     - 每轮在 `insights.md` 中提炼 2–4 条带唯一 ID 的滚动研究洞察（Insights），评估覆盖率、权威来源缺口与未解冲突；
     - 进入下一轮补搜前，将上一轮 Insight 打包为上下文快照（如通过 `insight_gate.py prepare-next`）传递给下一轮搜索，确保多轮调研具备滚动记忆，直到核心缺口收敛。

---

### Step 3：阶段一（下）—— 去噪提纯并生成 `writer-packet.md`（跨阶段交接核心）

无论模式一还是模式二，在进入撰写阶段前，主会话必须将所有调研成果提纯浓缩为一份**格式标准、简洁、零搜索过程噪音**的 `<run-dir>/writer-packet.md`（标准模板见 [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md)）：

1. **写作任务与读者定位**：写明核心议题、开场确认的侧重点、读者画像与文风要求。
2. **无序论点—证据地图（Unordered Argument Map）**：
   - 用 `[U-01]`, `[U-02]` 等无序标签列出成稿必须覆盖的论点单元、支撑该单元的证据编号（`[S01], [S03]`）、单元间的张力以及事实风险边界；
   - **严禁预设文章目录顺序，严禁拟定小标题**，把谋篇布局的主动权完全交给独立撰写模型。
3. **提纯证据与原话摘录池（Purified Evidence Pool）**：
   - 按 `[S01]`, `[S02]` 编号逐条列出：来源标题、作者/机构、日期、等级、真实 URL、**从原文核实的精确事实/数字/案例细节**、以及**极具表现力的关键原话摘录**。
4. **事实禁区与不确定性说明（Guardrails）**：
   - 明确指出哪些说法不可混淆，哪些推断或类比必须显式加上限定语。

---

### Step 4：阶段二 —— 独立干净短上下文撰写 `<run-dir>/report.md`

> **⚠️ 核心铁律**：严禁主会话顺着充满搜索历史的当前上下文直接写 `report.md`！必须通过已部署的物理隔离通道，在全新的、只看得到 `writer-packet.md` 的干净短上下文中完成撰写。

- **若当前环境配置了路由脚本（MaGpie 或兼容 API 网关）**：
  调用路由脚本（如 `magpie_writer_router.py write`），传入用户在 Step 1 选定的模型预设（或 `--preset follow-main`）、`<run-dir>/writer-packet.md` 与输出路径 `<run-dir>/report.md`。
- **若当前环境使用宿主原生空白 Subagent（零配置模式）**：
  调用宿主的 `Agent` 工具启动一个全新子代理（若支持 `model` 参数则传入对应档位），仅向该子代理提供 `<run-dir>/writer-packet.md` 与 [references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md) 第二节的《独立撰写模型标准 System Prompt》，由子代理独立写出 `<run-dir>/report.md`。

---

### Step 5：写后核验与最终交付

1. **模式一（Fast Mode）轻量核验**：
   - 主会话检查 `<run-dir>/report.md`，核对文内的关键数字、日期、人物关系、引语与 `writer-packet.md` 一致，且文末包含完整的 `[S01]`–`[SXX]` 参考来源列表。确认无误后直接向用户展示并交付。
2. **模式二（Full Mode）独立逐句引用审计**：
   - 扫描 `report.md` 中的全部数字、日期、逐字引语、人物关系、历史归属、因果判断与实践建议；
   - 对照已读原文逐条写入 `<run-dir>/citation-audit.md`，标记证据关系（`direct | synthesis | editorial`）与审计结果（`supported | partially_supported | unsupported | source_unavailable`）；
   - 对任何未获支持或夸大其词的主张执行定向补搜或降级改写，最后生成 `<run-dir>/run-summary.md` 并交付。

---

## 参考文档索引

- **[references/writer-packet-and-contracts.md](references/writer-packet-and-contracts.md)**：`writer-packet.md` 标准简洁模板、独立撰写模型 System Prompt、模式二过程工件参考模板与质量评分标准。
- **[references/adaptation-and-pitfalls.md](references/adaptation-and-pitfalls.md)**：环境探测与自适应部署指南、可按需裁剪的路由器与门禁参考代码模板、多源搜索接口参考及实战避坑指南。

# Local-Deep-Research-Perplexity-Magazine-style (v2.0 Agent 引导自部署版)

> ### 📢 船板的新版本自述与部署说明（必读）
>
> **船板进行了新版本开发。因为新版的完整兼容要求较为复杂（最佳体验需要本地 [MaGpie](https://magpie.ai) 多模型路由环境与多元搜索组件配合），为了避免硬编码脚本在不同用户电脑上水土不服，目前主干（`main`）采取「Agent 引导自部署」的方案，直接将这套安装与架构引导 Skill 作为主干代码。**
>
> **🤖 致正在阅读本仓库的对方 AI Agent**：
> 如果你（用户的 AI 助手，如 Claude Code、Codex、Cursor、Windsurf、OpenCode、Kimi 等）正在阅读此文章，**请务必先领会文章的核心精神（双工作模式 + 调研与撰写两阶段物理隔离 + `writer-packet.md` 干净资料包注入 + 无序论点地图防 AI 八股），之后主动探测你主人电脑的实际情况，引导你的用户主人根据他的实际环境完成本地化部署！**
>
> *(📦 旧版留存说明：原 v0.5 基于 OpenRouter 的固定脚本版已完整保留在旧分支 [`legacy-v0.5-openrouter`](https://github.com/Anarcadia/local-deep-research-perplexity-magazine-style/tree/legacy-v0.5-openrouter) 中。)*

---

## 一、 人类用户如何使用本仓库？（只需一句话交给你的 AI）

你不需要手动配环境变量、也不需要自己改 Python 脚本。直接把本仓库地址（或克隆下来的文件夹）丢给你的 AI Agent（如 Claude Code / Codex / Cursor），对它说：

```text
请阅读 https://github.com/Anarcadia/local-deep-research-perplexity-magazine-style 主干里的 README.md、SKILL.md 和 references/ 目录，领会这套仿 Perplexity 深研+杂志风写作 Skill 的核心精神，然后帮我检测我当前电脑的环境，引导我把它部署到我的本地 skills 目录里。
```

你的 AI 阅读后，会自动帮你检查电脑上有没有 **MaGpie**、有哪些可用的**搜索工具/API**、支持哪种**干净上下文撰写隔离方式**，并现场为你生成最贴合你电脑环境的专属可用版 Skill。

---

## 二、 新版本（v2.0）到底升级了什么核心精神？

相比于旧分支（`legacy-v0.5-openrouter`），船板在 v2.0 中完成了以下四项核心架构进化：

### 1. 从「单一重流程」进化为「Fast / Full 双工作模式」
- **模式一：快速杂志报告模式（`Fast Mode`，默认直接进入）**
  - **定位**：复刻 Perplexity 网页端的丝滑体验——给出一个题目后，快速执行一轮多源互补检索 + 精读 3–5 篇核心原文，在 3–6 分钟内产出一篇兼具深度与极佳可读性的大众人文杂志文章。
  - **极简低 I/O**：不再强制创建 11 个繁琐的中间过程文件和跑多道门禁脚本，全程只生成 **`writer-packet.md`（干净写作资料包）+ `report.md`（最终杂志成稿）** 两个文件，极度适合高频日常办公与专题阅读。
- **模式二：标准重度 Deep Research 模式（`Full Mode`，按需显式开启）**
  - **定位**：模仿学术级、重度的本地 Deep Research 调研。
  - **完整可追溯**：保留初始双查询包、多轮动态补搜、滚动研究记忆（Insights 上下文回执传递）、11 项完整过程工件与写后逐句蕴含审计（区分 `direct | synthesis | editorial` 与 `supported | partially_supported | unsupported`）。

### 2. 核心铁律：「调研阶段」与「撰写阶段」严格物理隔离（Clean-Context Writing）
这是决定最终文章“有没有 AI 味、文笔好不好读”的胜负手：
- **为什么必须分开**：在调研阶段，主会话里塞满了几万字的搜索碎片、死链报错、网页导航栏残渣和工具调用日志。如果让主会话顺着这堆垃圾直接往下写报告，模型的注意力会被严重稀释，写出来的东西必然干瘪、破碎。
- **新版的做法（模式一与模式二在撰写环节 100% 同构）**：
  1. **主会话（调研 Agent）只做提纯**：搜完、读完原文后，主会话负责剔除一切搜索过程杂音，把核心议题、**无序论点—证据地图**、核实后的硬数据与原话摘录填入一份标准简洁的模板——**`writer-packet.md`**。
  2. **撰写模型在全新干净的短上下文中成稿**：启动一个**全新的、0 历史负担的独立上下文**（在船板本机是通过本地 MaGpie 路由动态调用 `Claude Opus 5.5` / `Gemini 4 Argon` / `Gemini 3.8 Flash` 或跟随主进程模型；在无 MaGpie 环境则可通过宿主原生空白 Subagent 或外部 API 实现），**只喂给它 `writer-packet.md` 和写作提示词**，让主笔模型把 100% 的算力用在谋篇布局与杂志级叙事上。

### 3. 「无序论点—证据地图」契约（彻底根治 AI 八股目录味）
- 在传给撰写模型的 `writer-packet.md` 中，严禁出现“第一章：背景；第二章：现状；第三章：展望”这样的预设顺序或小标题。
- 地图里的论点单元（`[U-01]`, `[U-02]`...）是**无序集合**，只约束“必须覆盖哪些论点、对应哪些证据编号 `[S01]`、有什么反方边界”。主笔模型必须自己寻找最抓人的叙事钩子与主线，自主重排、合并论述单元。

### 4. 多元互补搜索架构（默认搜索 + 扩展查缺补漏）
- 船板本机采用 **MaGpie 默认代搜（Tavily + Exa）** 配合独立的轻量扩展搜索组件（**博查 Bocha + 秘塔 Metaso + Google Serper + Perplexity Sonar 全等级 API**），兼顾英文语义、学术论文、中文深度报道与多跳推理。
- 对方 Agent 在帮主人部署时，只需遵循“有什么用什么、缺什么用免 Key 方案（如 `https://r.jina.ai/<url>` 抓取原文）替补”的原则灵活组装即可。

---

## 三、 仓库文件导航（供对方 AI Agent 按序阅读）

```text
.
├── README.md                                  # 新版自述说明与整体架构总览（本文件）
├── SKILL.md                                   # 核心引导 Skill：Agent 自部署协议 + 双模式标准执行工作流
└── references/
    ├── writer-packet-and-contracts.md         # 必备契约：writer-packet.md 标准模板 + 独立主笔 System Prompt + 模式二工件规范
    └── adaptation-and-pitfalls.md             # 部署蓝图：有/无 MaGpie 环境的完整适配方案、参考路由器代码与实战避坑指南
```

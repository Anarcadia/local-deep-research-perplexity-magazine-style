# Local-Deep-Research-Perplexity-Magazine-style

## 简介

本 Skill 通过逆向分析 Perplexity 网页端 Deep Research Agent 的运行模式，在本地使用多元搜索 API，实现仿 Deep Research 的工作流。其主旨不在于实现严谨、学术化、以最高可验证性和准确率为目标的 Deep Research，而是要实现本地较快速、通俗的知识调研和科普/人文风味文章写作，让用户获得优质的学习与阅读体验，避免受到严重的AI写作风味干扰。

工作流将搜索 Agent 和写作 Agent 的模型分离：研究模型负责搜集、阅读和组织证据，另行选择更擅长自然表达的模型完成通俗易懂、易于阅读的科普杂志风格写作。Skill 内部预置 OpenRouter 后端接口，以及 GLM-5.2、Gemini 3.1 Pro Preview、Claude Opus 4.6 和 Claude Sonnet 5 模型选择项。

Skill初始化时有详尽的选择路由，建议用户选择使用 Claude Sonnet 5 或 Gemini 3.1 Pro Preview 执行写作任务，若SKill出现问题未能及时询问用户，建议用户主动指定SKill使用何种搜索工具或者写作模型以取得最佳效果哦。

若用户的 OpenRouter 账号因地区限制无法使用 OpenAI、Anthropic 或 Google 模型，可以切换为 GLM-5.2，也可以让 Agent 改用其他可用模型 ID，或将接口替换为其他 OpenAI 兼容的模型供应商，例如 `zenmux`。

本 Skill 默认可以使用宿主 Agent 自带的网络搜索；Exa、Perplexity、Grok Build 和 KimiCode 在完成配置前保持关闭。

## Insight 递归机制

每轮调研都会强制产生 2–4 条带唯一 ID 的 Insight，并记录形成它们的查询、来源、冲突、待补缺口和停止指标。没有合格 Insight，流程不能进入下一轮或开始写作。

进入下一轮前，Skill 会把上一轮完整 Insight 写成带哈希的上下文包并生成送达回执。下一轮每个搜索动作都要记录自己收到的 Context ID，以及它对该动作的实际影响：采用、看过但未采用、被新证据反驳，或仅作为背景。这个机制确保 Insight 被产生、被送达并且可追溯，但不强迫搜索 Agent 按照 Insight 行动。

Insight 不是事实来源，也不要求进入最终文章。正文仍只使用经过来源账本和引用审计核验的外部材料。

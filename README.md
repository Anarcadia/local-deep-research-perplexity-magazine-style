# Local-Deep-Research-Perplexity-Magazine-style

## 简介

本 Skill 通过逆向分析 Perplexity 网页端 Deep Research Agent 的运行模式，在本地使用多元搜索 API，实现仿 Deep Research 的工作流。其主旨不在于实现严谨、学术化、以最高可验证性和准确率为目标的 Deep Research，而是要实现本地较快速、通俗的科普文章写作。

工作流将搜索 Agent 和写作 Agent 的模型分离：研究模型负责搜集、阅读和组织证据，另行选择更擅长自然表达的模型完成通俗易懂、易于阅读的科普杂志风格写作。Skill 内部预置 OpenRouter 后端接口，以及 GLM-5.2、Gemini 3.1 Pro Preview、Claude Opus 4.6 和 Claude Sonnet 5 模型。建议使用 Claude Sonnet 5 或 Gemini 3.1 Pro Preview 执行写作任务。若 OpenRouter 账号因地区限制无法使用 OpenAI、Anthropic 或 Google 模型，可以切换为 GLM-5.2，也可以让 Agent 改用其他可用模型 ID，或将接口替换为其他 OpenAI 兼容的模型供应商，例如 `zenmux`。

本 Skill 默认可以使用宿主 Agent 自带的网络搜索；Exa、Perplexity、Grok Build 和 KimiCode 在完成配置前保持关闭。

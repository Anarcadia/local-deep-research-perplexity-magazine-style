# 核心契约、模板与质量标准全集（Contracts, Artifacts & Quality Rubric）

> 本文件是 `local-deep-research` 系统的完整模板与契约参考，100% 独立自包含。包含：
> 1. 跨阶段交接核心：**`writer-packet.md`（干净写作资料包）** 标准模板；
> 2. 阶段二：**独立撰写模型的标准 System Prompt 与 User Message 契约**；
> 3. 模式二（标准重度深研 Full Mode）：**全部 11 项过程工件的完整字段模板**；
> 4. **来源分级、主张分类、引用蕴含审计与杂志叙事质量标准（Quality Rubric）**。

---

## 一、 `writer-packet.md` 标准简洁模板（模式一与模式二通用）

无论执行的是「模式一：快速杂志报告（Fast Mode）」还是「模式二：标准重度深研（Full Mode）」，在阶段一（调研）结束、进入阶段二（独立撰写）之前，主会话（调研模型）必须将所有有效材料**去噪提纯**，按以下 4 个模块写入 `<run-dir>/writer-packet.md`。

**核心要求**：此文件是传入独立撰写模型的**唯一事实依据**，严禁混入搜索过程日志、死链报错、网页导航栏乱码或无关摘要。

```markdown
# Writer Packet（干净写作资料包）

## 1. 写作任务与读者定位
- **核心议题**：<一句话清晰界定本次报告要回答的中心问题与用户在开场确认的侧重点>
- **目标读者与视角**：<如：关注技术、商业或人文演进的大众深度读者 / 行业研究者>
- **时效与语境基准**：<标明当前时间基准与核心语境>
- **文风与特殊要求**：<未指定时写“采用默认大众人文杂志讲述型写法，语言自然流动，避免列表堆砌，使用规范全角中文标点”；若用户有明确文风/结构要求则在此写明>

## 2. 无序论点—证据地图（Unordered Argument Map）
> **写作契约**：以下论述单元为【无序集合】，仅用于约束成稿必须覆盖的论点、证据对应关系与张力边界。
> 撰写模型【严禁】将本表顺序当作章节目录，也【严禁】照抄单元 ID 或内部标签作为小标题。请先独立判断中心问题与最佳叙事主线，自主重排、合并或拆分论述单元，并独立拟定最契合文章气质的总标题与小标题。

- **[U-01]** 必选论点/待答问题：<用中性语言描述该单元要讲透的核心问题>
  - **支撑证据 IDs**：[S01], [S03]
  - **与其他单元的张力/关系**：<如：与 U-03 的乐观预期构成现实成本反差>
  - **事实风险与限定边界**：<如：仅在特定样本验证，不可外推为普适定律>

- **[U-02]** 必选论点/待答问题：...
  - **支撑证据 IDs**：[S02], [S04]
  - **与其他单元的张力/关系**：...
  - **事实风险与限定边界**：...

- **[U-Counter]** 反方校正与争议视角：...
  - **支撑证据 IDs**：[S05]
  - **事实风险与限定边界**：...

## 3. 提纯证据与原话摘录池（Purified Evidence Pool）
> **引用准则**：正文中出现的所有关键数字、日期、人物关系、直接引语和因果机制，必须严格源自下方证据池，并在文内标注 `[S01]` 等角标，文末附完整来源列表。

- **[S01]** 《来源标题》（作者/机构，发布日期，等级 A/B/C，URL）
  - **核心核实事实/数据**：<精炼列出已从原文核实的硬数据、时间点、案例细节与机制事实>
  - **关键原话/段落摘录**：<极具表现力的原话引语或精确段落内容>
  - **证据属性**：`direct`（直接事实） | `source_view`（特定作者观点） | `synthesis_premise`（综合推断前提）

- **[S02]** 《来源标题》（作者/机构，发布日期，等级 A/B/C，URL）
  - **核心核实事实/数据**：...
  - **关键原话/段落摘录**：...
  - **证据属性**：...

## 4. 事实禁区与不确定性说明（Guardrails & Uncertainties）
- **严禁混淆的边界**：<明确指出调研中发现容易被误传、夸大或张冠李戴的说法>
- **需降级表述的推断/类比**：<哪些跨领域连接或推演必须显式加上“有研究者认为”“可作类比”“尚存争议”等限定语>
- **已知材料缺口**：<若有未公开或无法核实的数据，要求在文中诚实交代而非猜测>
```

---

## 二、 阶段二：独立撰写模型的标准 System Prompt 与 User Message

当通过路由脚本（如 `magpie_writer_router.py`）或原生空白 Subagent 启动独立撰写阶段时，固定向撰写模型注入以下提示词：

### 1. 标准 System Prompt
```text
你是一位顶级深度杂志主笔。你当前运行在独立的「纯净撰写阶段（Clean-Context Writing Stage）」。
你的全部事实依据仅限于下方提供的《Writer Packet（干净写作资料包）》。

【文风与排版准则】
除非资料包中另有明确指定，务必使用地道中文，报刊杂志、非学术、大众人文杂志，讲述型的写法去撰写报告，语言自然流动、避免列表清单，图表需要控制出现频率，写作根据内容可以尽可能详细展现，字数不限制。使用规范的全角中文标点，不使用半角英文逗号、冒号或引号代替中文标点；标题和正文都应符合正式中文出版物的排版习惯。

【叙事结构与防八股契约】
除非用户明确指定文章结构，输入的「无序论点—证据地图」仅是无序的论点与证据集合，绝不是文章目录。不要沿用其行顺序、单元标签或研究素材措辞作为章节顺序、标题和固定表达。请先独立判断中心问题与最佳叙事主线，自主重排、合并或拆分论述单元，并拟定更适合成稿的总标题和小标题；同时覆盖全部必选论点，严格遵守证据池与事实禁区的边界，不得虚构未在资料包中提供的事实或数字。

【引用与输出要求】
在正文中引用具体事实、数据或原话时保留 `[S01]` 格式的引用标记，并在文章末尾附上对应的「参考与证据来源」列表（含标题与 URL）。直接输出完整的最终成稿 Markdown 正文，不要输出任何开场寒暄、自我解释或过程说明。
```

### 2. 标准 User Message 包装格式
```text
请基于以下经过去噪提纯的《Writer Packet（干净写作资料包）》，独立构思叙事主线并完成整篇深度报告撰写：

=== BEGIN CLEAN WRITER PACKET ===
<此处插入 writer-packet.md 全文>
=== END CLEAN WRITER PACKET ===
```

---

## 三、 模式二（标准重度深研 Full Mode）全套 11 项过程工件字段模板

- **模式一（Fast Mode，默认）**：在 `<run-dir>` 下**只生成 `writer-packet.md` + `report.md` 两个文件**。
- **模式二（Full Mode，学术级重度深研）**：在 `<run-dir>` 下维护以下完整工件体系（外加写前生成的 `writer-packet.md`）：

### 1. `brief.md`
```markdown
# Research Brief
- 原始请求：
- 工作模式：Full Mode（标准重度深研）
- 选定撰写模型预设：opus-5.5 | sonnet-5.5 | gemini-4-argon | gemini-3.8-flash | follow-main
- 核心问题与开场澄清焦点：
- 必选维度：
- 立场与反方校正：
- 读者/文体/长度：
- 时效与语言：
- 外部视角覆盖计划：权威/原始资料｜专业语义来源｜中国国内信息｜海外用户/草根｜社交媒体/社区｜反方
```

### 2. `research-map.md`
```markdown
| ID | 子问题 | 类型 | 状态 | 关键 claims | 缺口 |
|---|---|---|---|---|---|
```
- **类型**：`required | optional | counterpoint`
- **状态**：`open | partial | covered | blocked`

### 3. `query-log.md`
```markdown
| Round | Pack | Query ID | Query | 职责 | 工具 | 结果数 | Source IDs | Insight Context | Context influence | 时间 | 备注 |
|---|---|---|---|---|---|---:|---|---|---|---|---|
```
- **规则**：`Round` 写 `R1`, `R2`...；Round 1 的 `Insight Context` 固定填 `initial-brief`；Round 2 起必须填 `insight_gate.py prepare-next` 生成的 `CTX-R2-xxxxxxxx`；`Context influence` 必须为 `used | considered-not-used | countered | background-only` 之一。

### 4. `sources.jsonl`
每行一个 JSON 对象：
```json
{"source_id":"S001","url":"","title":"","domain":"","date":"","language":"","grade":"A|B|C|D","status":"discovered|shortlisted|read|cited|verified","discovered_by":["A1"],"questions":[],"summary":"","evidence_locator":"","limitations":""}
```

### 5. `insights.md`（受 `insight_gate.py` 强制校验）
```markdown
## Round 1
- 输入查询 IDs：A1, A2, A3, B1, B2, B3
- 输入来源 IDs：S001, S002, S003
- Insight I-R1-01：...
- Insight I-R1-02：...
- 新概念：...
- 冲突/不确定性：...
- 候选下一轮缺口：...
- coverage：0.60
- authority_gap：2
- open_conflicts：1
- perspective_gap：1
- systematic_gap：0
- high_value_delta：4
- 新增高价值 Claim IDs：C01, C02, C03, C04
```
- **门禁要求**：每轮必须包含 **2–4 条** Insight，ID 格式严格为 `I-R<轮次>-<两位序号>`（如 `I-R1-01`）；下方 12 个必填字段缺一不可。

### 6. `insight-context.jsonl` 与 `round-context/`
- 由 `python3 <skill-dir>/scripts/insight_gate.py prepare-next --run-dir <run-dir> --from-round <N> --next-round <N+1> --agent <name>` 自动生成。
- 保存上一轮 Insight 的 SHA256 快照与送达回执，确保下一轮搜索动作已看见上轮研究记忆。

### 7. `evidence-ledger.md`
```markdown
| Claim ID | 主张 | 类型 | 支持来源 | 反对来源 | 置信度 | 验证状态 | 可用论述单元 |
|---|---|---|---|---|---|---|---|
```
- **类型**：`fact | source_view | analogy | inference | uncertainty`
- **验证状态**：`unverified | supported | partially_supported | unsupported | source_unavailable`

### 8. `outline.md`
```markdown
# Argument Map

> 这是无序的论点—证据地图，不是文章目录。单元 ID 和标签只用于覆盖检查，不得直接用作章节标题，也不规定成稿顺序。

| 单元 ID | 必选 | 要回答的问题/论点 | Claim IDs | 与其他单元的关系或张力 | 风险边界 |
|---|---|---|---|---|---|
```
- 在 `insight_gate.py validate-run` 通过后，主会话将 `outline.md` + `evidence-ledger.md` + 已读来源原话提纯组装为 `writer-packet.md`，交由独立撰写模型生成 `report.md`。

### 9. `citation-audit.md`（写后逐句蕴含审计表）
```markdown
| Claim ID | 报告定位 | 引用 | 证据关系 | 审计结果 | 短摘录/页码/章节 | 修复动作 |
|---|---|---|---|---|---|---|
```
- **证据关系**：
  - `direct`：来源原文直接包含该事实或判断，才可标 `supported`；
  - `synthesis`：多个来源支撑各自前提，但连接是本报告的综合推断，通常标 `partially_supported`，并在正文说明是综合推断；
  - `editorial`：实践建议或价值判断，通常标 `partially_supported`，说明证据只支持其前提。
- **审计结果**：`supported | partially_supported | unsupported | source_unavailable`

### 10. `run-summary.md`
```markdown
# Run Summary
- 工作模式与撰写模型：
- 查询包/查询数：
- 候选/已读/引用/验证来源数：
- A/B/C/D 来源等级分布：
- 全部可证伪主张数：
- direct/synthesis/editorial 分布：
- supported/partially_supported/unsupported 分布：
- 修复轮数与动作：
- 停止理由：
- Insight 轮数与门禁状态：
- 已知限制与剩余不确定性：
```

---

## 四、 来源分级与叙事质量标准（Quality Rubric）

### 1. 来源等级（Source Grading）
- **A 级**：原始文献/一手数据、同行评审论文、政府与国际官方机构公报、正式行业标准。
- **B 级**：知名大学/研究智库报告、学术出版社专著、可靠专业组织、严谨的深度调查报道或核心当事人深度长访谈。
- **C 级**：一般主流媒体报道、百科词条、专业领域优质长文博客。
- **D 级**：普通论坛帖子、社交媒体讨论、营销推广页、无明确信源的视频或二手转述。
  - *铁律*：D 级来源可用于呈现大众情绪、社区争议或草根经验，但**绝不能单独支撑核心客观事实**。

### 2. 杂志叙事质量标准
- **开篇抓人但不虚构**：可以用极具反差感的具体人物切面、真实实验或历史瞬间开篇，但每一个细节都必须有证据池支撑。
- **围绕认知冲突推进，拒绝结果堆砌**：段落之间靠“提出问题 → 揭示张力 → 展现机制 → 反转或深化认知”的逻辑流转，而不是把搜到的资料按“第一、第二、第三”罗列。
- **事实、观点与类比边界分明**：传统掌故、特定学者一家之言、跨学科类比，必须在行文中自然嵌入“传统上归于”“正如某学者所言”“如果借用一个类比”等信号词，不把推演包装成已证实的定律。

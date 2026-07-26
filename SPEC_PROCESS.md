# SPEC_PROCESS.md — 规约与计划过程文档

## 一、Brainstorming 关键节点

### 节点 1：项目方向选择

用户要求分析 A（Coding Agent Harness）和 B（应用类项目）两个方向。我对比了两个方向的深度、评价标准、学习价值后推荐 A。用户确认选 A。

**关键追问**：用户问"只针对 Python 算一个 harness 吗"。我澄清了 harness 的本质——它是 agent 基础设施层（主循环、工具、治理、反馈、记忆、配置），不是目标语言的广度。目标语言只是 agent 操作的对象。用户接受。

### 节点 2：六维度合规检查

用户多次要求"根据作业要求检查设计"。第一次检查发现架构只有 5 个模块，**缺失记忆、反馈、配置三个维度**。修正为 7 模块架构。

第二次检查发现：
- LLM 响应格式未定义（parser 无法设计）
- 停机判断逻辑未设计
- 动作数据模型缺失
- 跨会话记忆持久化缺失
- 反馈客观判定缺失
- 测试策略缺失

全部补充后形成 10 模块的修正架构。

### 节点 3：SPEC 审阅

用户要求对照两份作业要求逐条审阅 SPEC。发现 7 个问题：
1. Session.history 类型不一致（§3.7 vs §6.1）
2. "更新" key 流程未明确（§3.1 要求"查看/更新/清除"）
3. LLM API 重试策略未定义
4. run_shell 超时未定义
5. write_file 路径安全缺失
6. Anthropic/Google provider 定位不明
7. 机制演示具体形式未说明

全部修复后提交。

### 节点 4：PLAN 审阅

用户要求对照对话内容和作业要求审阅 PLAN。发现 3 个问题：
1. Dockerfile 顺序错误（pip install 在 COPY 源码之前）
2. Task 6 标注 "Create" 但文件已被 Task 1 创建（应为 "Modify"）
3. 文件日志未实现（SPEC 要求输出到 .harness/logs/ 文件）

全部修复后提交。

---

## 二、关键迭代对话节选

### 迭代 1：架构从 5 模块到 7 模块

**AI 提出**：初始架构有 5 个模块（agent_loop, llm, tools, governance, cli）。

**用户**："请根据设计原则再次自检以下设计"

**AI 自检发现**：缺失记忆、反馈、配置三个维度，违反 A.4-D"六个维度都要有可运行的最低实现"。

**处理决策**：修正为 7 模块架构，补齐六维度。

### 迭代 2：数据模型与解析器设计

**用户**："针对 mvp 的各项功能再次进行设计的检查"

**AI 自检发现**：Message/Conversation/Session 模型缺失、LLM 响应格式未定义、错误处理策略未定义、工具注册机制未定义、配置 schema 未定义、日志缺失。

**处理决策**：补充 models.py（含 Message/Conversation/Session）、定义 JSON 响应格式契约、三级错误处理策略、ToolRegistry 模式、YAML config schema、Python logging。

### 迭代 3：SPEC 合规审阅

**用户**："请再次根据作业要求对这个 spec 文档进行审阅"

**AI 审阅发现**：Session.history 类型不一致、"更新"key 流程缺失、LLM 重试策略缺失、shell 超时缺失、write_file 路径安全缺失、provider 定位不明、演示形式不明。

**处理决策**：逐条修复，7 个问题全部解决。

---

## 三、AI 建议采纳与推翻

### 采纳的 AI 建议

1. **两阶段交付**：AI 提出先 MVP 再深化反馈闭环，用户采纳。
2. **反馈闭环作为重点维度**：AI 推荐并说明理由（最适合 coding 场景、最容易 mock 测试），用户采纳。
3. **Docker + PyPI 双形态分发**：AI 推荐，用户采纳。
4. **keyring 跨平台凭据存储**：AI 推荐，用户采纳。
5. **JSON 格式 LLM 响应契约**：AI 设计，用户采纳。

### 用户推翻/修正的

1. **用户要求多次自检**：AI 初始设计未主动对照作业要求检查，用户多次要求后才进行。这暴露了 AI 倾向于"快速推进"而非"严格合规"。
2. **用户澄清 WebUI 豁免**：AI 认为"必须提供 WebUI"与 CLI 项目冲突，用户澄清"如做带服务端的项目"才需要，CLI 豁免。

---

## 四、冷启动验证（§4.5）

### 操作方式

- **主开发 agent**：OpenCode（glm-5.2 模型）
- **冷启动 agent**：OpenCode general subagent（全新 session，不导入任何先前对话或 memory）
- **提供的材料**：仅 SPEC.md + PLAN.md，不补充口头解释
- **指定任务**：Task 2（Data Models）和 Task 5（Parser）
- **指令**：遇到不确定之处即暂停询问，而非凭猜测继续

### Subagent 暂停并提问的位置

Subagent 在读完 SPEC 和 PLAN 后，**暂停并提出了 2 个问题**：

1. **Task 1 依赖未满足**："Task 2 和 Task 5 依赖 Task 1（scaffolding），但项目当前没有 harness/、tests/ 等目录。是否应先实现 Task 1？"
   - **分析**：这不是 spec 缺陷，而是冷启动验证只指定了 Task 2 和 Task 5。但 subagent 正确识别了依赖关系，说明 PLAN 的依赖图清晰。
   - **处理**：批准先实现 Task 1。

2. **pytest 未安装**："环境中没有 pytest，是否应安装？"
   - **分析**：环境问题，非 spec 缺陷。
   - **处理**：批准安装。

### Spec 缺陷暴露

**无 spec 缺陷暴露。** Subagent 明确表示："No ambiguities in the SPEC/PLAN content itself for Task 2 and Task 5 — the code is fully specified."

### 与原意不一致的解读

**无不一致解读。** Subagent 严格按 PLAN 中的代码实现，未做任何 PLAN 外的假设。

### 产出与预期差距

**零差距。** Subagent 实现了 12 个文件，12/12 测试全部通过，3 次 commit 均符合 PLAN 要求。

### Subagent 的观察

Subagent 提出一个 minor note（非错误）：parser 的贪婪正则 `\{.*\}` 从第一个 `{` 匹配到最后一个 `}`，如果响应包含两个独立的顶层 JSON 对象会出错。但所有 5 个测试用例通过，且与 PLAN 完全一致。

### 据此对 SPEC/PLAN 的修订

**无需修订。** 冷启动验证证明 SPEC 和 PLAN 质量足够高，陌生 agent 可仅凭文档无歧义地实现任务。

### 反思

**brainstorming 技能做得好的地方**：
- 分块呈现设计、逐节确认，避免了"一次性输出大量内容后才发现问题"
- 多次自检机制（虽然由用户触发）有效捕获了合规性缺口

**brainstorming 技能让我不满的地方**：
- 初始设计未主动对照作业要求，依赖用户多次要求才进行合规检查
- 架构设计阶段过于关注"模块划分"而忽略了"模块间通信的数据模型"，导致后续需要补充

---

## 五、Phase 2 Brainstorming 过程

### 背景

Phase 1（MVP）完成后，用户要求"继续根据 superpowers 的流程完成后续补充"。我重新审阅了所有 md 文档和作业要求，确定了 Phase 2 方向为反馈闭环深化。

### 方案选择

提出 3 个方案：
- A: 后置钩子（~50 行，改动最小）
- B: 反馈流水线（~150 行，通用可扩展）
- C: 完整闭环（~300 行，流水线 + 自修正 + 模式检测）

用户选 C（完整闭环）。

### 设计审阅与修复

设计文档初版有 4 个问题，在用户要求"重新检查实现思路"后发现并修复：

1. **"自修正"概念混淆**：设计文档写了 `_try_auto_fix()` 函数，但 harness 无法自己修复语法错误——这需要 LLM 智能。修复为"增强反馈注入驱动 LLM 自修正"。
2. **模式分析读错字段**：`fb.raw_result.metadata.get("tool")` 应为 `action.tool`（从 history 元组取）。
3. **与 SPEC 不对齐**：SPEC §11.6 承诺了 typecheck/coverage/HITL 状态机等，但设计只覆盖了 syntax check + pattern analysis。明确标注 scope cut。
4. **未提及更新 SPEC**：实现 Phase 2 后应同步更新 SPEC §3.6 和 §11.6。

### 反思

Phase 2 的 brainstorming 暴露了一个问题：设计文档的"自修正"概念在初版中是错误的。原因是我在写设计时没有严格区分"harness 能做什么"和"LLM 能做什么"——harness 只能检测和注入 hint，修复是 LLM 的职责。这个概念混淆如果没被发现，会导致 writing-plans 产出一个无法实现的 task（`_try_auto_fix` 函数体为空）。

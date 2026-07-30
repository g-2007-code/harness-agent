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

### §四-A：OpenCode 子 agent 冷启动（首次验证）

#### 操作方式

- **主开发 agent**：OpenCode（glm-5.2 模型）
- **冷启动 agent**：OpenCode general subagent（全新 session，不导入任何先前对话或 memory）
- **提供的材料**：仅 SPEC.md + PLAN.md，不补充口头解释
- **指定任务**：Task 2（Data Models）和 Task 5（Parser）
- **指令**：遇到不确定之处即暂停询问，而非凭猜测继续
- **局限说明**：此验证使用同一平台（OpenCode）内的 subagent，未满足"第二个智能体类型必须不同"的要求。结果仅验证了"同平台内文档可读性"，未验证"跨平台文档完整性"。

#### Subagent 暂停并提问的位置

Subagent 在读完 SPEC 和 PLAN 后，**暂停并提出了 2 个问题**：

1. **Task 1 依赖未满足**："Task 2 和 Task 5 依赖 Task 1（scaffolding），但项目当前没有 harness/、tests/ 等目录。是否应先实现 Task 1？"
   - **分析**：这不是 spec 缺陷，而是冷启动验证只指定了 Task 2 和 Task 5。但 subagent 正确识别了依赖关系，说明 PLAN 的依赖图清晰。
   - **处理**：批准先实现 Task 1。

2. **pytest 未安装**："环境中没有 pytest，是否应安装？"
   - **分析**：环境问题，非 spec 缺陷。
   - **处理**：批准安装。

#### Spec 缺陷暴露

**无 spec 缺陷暴露。** Subagent 明确表示："No ambiguities in the SPEC/PLAN content itself for Task 2 and Task 5 — the code is fully specified."

#### 与原意不一致的解读

**无不一致解读。** Subagent 严格按 PLAN 中的代码实现，未做任何 PLAN 外的假设。

#### 产出与预期差距

**零差距。** Subagent 实现了 12 个文件，12/12 测试全部通过，3 次 commit 均符合 PLAN 要求。

#### Subagent 的观察

Subagent 提出一个 minor note（非错误）：parser 的贪婪正则 `\{.*\}` 从第一个 `{` 匹配到最后一个 `}`，如果响应包含两个独立的顶层 JSON 对象会出错。但所有 5 个测试用例通过，且与 PLAN 完全一致。

#### 据此对 SPEC/PLAN 的修订

**无需修订。** 冷启动验证证明 SPEC 和 PLAN 质量足够高，陌生 agent 可仅凭文档无歧义地实现任务。

---

### §四-B：GitHub Copilot 跨平台冷启动验证（补充验证）

#### 背景

首次验证使用同一平台（OpenCode）的 subagent，不满足 §4.5"第二个智能体类型必须不同"的要求。后续使用 GitHub Copilot 作为独立智能体，在全新 session、不导入任何对话历史的前提下，仅凭 SPEC.md + PLAN.md 尝试实现任务。

#### 操作方式

- **主开发 agent**：OpenCode（glm-5.2 模型）
- **冷启动 agent**：GitHub Copilot（完全不同平台和模型，无共享上下文）
- **提供的材料**：仅 SPEC.md + PLAN.md（与首次验证相同版本）
- **指定任务**：Task 1（Project Scaffolding）和 Task 2（Data Models）
- **指令**：与首次验证相同——遇到不确定之处即暂停询问，而非凭猜测继续

#### 实现结果

Copilot 成功完成了 Task 1 和 Task 2，产出文件：

| 文件 | 状态 | 说明 |
|------|------|------|
| `pyproject.toml` | ✅ 创建 | 与 PLAN 一致 |
| `.gitignore` | ✅ 创建 | 标准 Python 忽略规则 |
| `harness/__init__.py` | ✅ 创建 | 包初始化 |
| `harness/llm/__init__.py` | ✅ 创建 | 空 docstring |
| `harness/tools/__init__.py` | ✅ 创建 | 空 docstring |
| `tests/__init__.py` | ✅ 创建 | 空文件 |
| `tests/conftest.py` | ✅ 创建 | tmp_project_dir fixture |
| `harness/models.py` | ✅ 创建 | 数据模型 |
| `tests/test_models.py` | ✅ 创建 | 7 个测试 |
| `config.yaml` | ✅ 创建 | 默认配置 |

#### 暴露的 Spec 缺陷

**缺陷 1：`build-backend` 值在 PLAN 中是错误的**

Copilot 的 `pyproject.toml` 使用了 `build-backend = "setuptools.backends._legacy:_get_build_requires"`，这与 PLAN 中的代码一致。但**这个值在实际运行中无效**——主项目 Phase 1 的 subagent 在实现时才发现并修复为 `build-backend = "setuptools.build_meta"`。

- **根因**：PLAN 中的代码在"理想环境"中编写，未实际运行验证。`build-backend` 错误是 Phase 1 中唯一一个 PLAN 代码错误，此处被 Copilot 复现，证明**该错误具有可重现性**。
- **修复**：主项目通过 `84654c0` commit 修复。
- **结论**：**SPEC 和 PLAN 应显式标注"已知坑位"**，尤其是 PLAN 中包含的代码片段应经过实际运行验证。

**缺陷 2：Phase 2 数据模型扩展在 SPEC 中无显式标注**

Copilot 的 `models.py` 缺少以下字段：
- `ActionResult.metadata`（Phase 2 新增）
- `CheckResult` 类（Phase 2 新增）
- `Feedback.checks`、`Feedback.suggested_next_action`、`Feedback.turn_number`（Phase 2 新增）
- `Config.llm_base_url`（Phase 1 DeepSeek 支持新增）

- **根因**：SPEC 的 §6（数据模型）只列出了 MVP 版本，但 §11（领域与机制设计）和 §12（两阶段交付计划）中描述的 Phase 2 扩展没有同步更新到 §6 的数据模型定义中。一个仅凭 SPEC 实现的 agent 无法知道这些字段需要存在。
- **结论**：**数据模型应在一处统一定义，各阶段扩展应标注版本**。当前 SPEC 中数据模型分布在 §6（核心模型）和 §11（领域设计）两处，易导致遗漏。

#### 与原意不一致的解读

1. **类型提示差异**：Copilot 的 `Action.args` 使用 `Dict[str, object]`，主项目使用 `dict`。功能等价，风格不同。
2. **Feedback 模型缺少 `field(default_factory=list)`**：Copilot 的 `Feedback.checks` 没有默认值，主项目有 `field(default_factory=list)`。运行时如果 `checks` 参数缺失会报错。
3. **SPEC.md 和 PLAN.md 被 Copilot 完整复制**：Copilot 将 SPEC.md 和 PLAN.md 直接复制到同名文件，说明它认为"文档也属于项目交付物"——这与主开发 agent 的理解一致，但 Copilot 未对文档内容做任何修改或补充。

#### 产出与预期差距

- Copilot 完成了 **2 个 task**（Task 1 和 Task 2），共 **10 个文件**
- 主项目共完成 **24 个 task**（16 Phase 1 + 8 Phase 2），共 **50+ 个文件**
- Copilot 未推进到 Task 3 之后的任务，原因可能是：Task 2 之后的任务依赖更多模块，Copilot 在缺乏上下文的情况下无法独立决策
- Copilot 的 `models.py` 缺少 Phase 2 扩展字段，与其 SPEC §11 的描述不一致

#### 据此对 SPEC/PLAN 的修订

1. **PLAN 中的代码片段应标注"已验证"**：`build-backend` 的实际有效值应替代 PLAN 中的错误值，或在 task 描述中注明"此值在 Windows 上已验证，XX 为无效值"。
2. **SPEC 的数据模型应集中定义**：将 §11 中描述的 Phase 2 扩展字段合并到 §6 的数据模型表格中，并标注"Phase 2 新增"。
3. **添加跨平台兼容性说明**：Windows 上的路径转义、命令语法差异应在 SPEC 中显式标注。

#### 两次验证的对比总结

| 维度 | §四-A OpenCode subagent | §四-B GitHub Copilot |
|------|------------------------|---------------------|
| 平台 | 同一平台 | 不同平台 |
| 完成 task | 2 个（Task 2 + Task 5） | 2 个（Task 1 + Task 2） |
| Spec 缺陷 | 无 | 2 个（build-backend 错误、数据模型分散） |
| 测试通过率 | 12/12 | 7/7 |
| 偏差 | 无 | 类型提示、Feedback 默认值 |

#### 验证结论

**单平台验证不足以发现 SPEC 缺陷。** 首次验证（OpenCode subagent）报告"无 spec 缺陷"，但跨平台验证（GitHub Copilot）暴露了 2 个真实缺陷。§4.5 要求"第二个智能体类型必须不同"是有道理的——不同平台对文档的解读方式不同，暴露的问题也不同。

**PLAN 中的代码必须实际运行。** 两个 agent 都直接使用了 PLAN 中的 `build-backend` 错误值，说明"从文档直接复制代码"是 agent 的默认行为。如果文档中的代码未经实测，错误会直接传播到实现中。

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

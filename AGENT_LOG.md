# AGENT_LOG.md — 实现过程日志

> 按时间顺序记录关键节点，每条包含时间戳、task 编号、触发的 Superpowers 技能、关键 prompt/context 配置、subagent 输出片段或 commit hash、人工干预、教训。

---

## 阶段一：规约与计划（brainstorming + writing-plans）

### 2026-07-08 — brainstorming 启动

- **技能**：`brainstorming`
- **操作**：读取三个作业文档，分析 A/B 两个方向，推荐 A（Coding Agent Harness）
- **关键决策**：
  - 语言：Python
  - LLM：可插拔（OpenAI + DeepSeek via base_url + Mock）
  - 重点维度：反馈闭环
  - 目标场景：Python 项目专用 coding agent
  - 交互方式：CLI
  - 分发：Docker + PyPI
  - 凭据：keyring 跨平台存储
- **人工干预**：用户多次要求"根据作业要求检查设计"，触发合规性自检，发现初始架构缺失记忆/反馈/配置三个维度

### 2026-07-08 — SPEC.md 编写与自审

- **技能**：`brainstorming` → spec self-review
- **commit**：`169aa4e`（SPEC.md 初版）、`7f56145`（自审修复）
- **自审修复 6 个问题**：
  1. parser 输出与 Action 模型一致性
  2. 组件图 GovernanceDecision 字段名
  3. Session.history 类型补全
  4. parser JSON 提取规则明确化
  5. governance 匹配规则明确化
  6. Docker keyring 配置方案

### 2026-07-08 — 作业要求二次审阅

- **用户要求**："请再次根据作业要求对这个 spec 文档进行审阅"
- **审阅修复 7 个问题**：
  1. Session.history 类型不一致（§3.7 vs §6.1）
  2. "更新"key 流程未明确
  3. LLM API 重试策略未定义
  4. run_shell 超时未定义
  5. write_file 路径安全缺失
  6. Anthropic/Google provider 定位不明
  7. 机制演示具体形式未说明

### 2026-07-08 — PLAN.md 编写与自审

- **技能**：`writing-plans`
- **commit**：`109148e`（PLAN.md 初版）、`6760a08`（自审修复）
- **16 个 Task**，每个含完整 TDD 步骤（写测试→验证失败→实现→验证通过→commit）
- **自审修复 3 个问题**：
  1. Dockerfile 顺序错误
  2. Task 6 文件标注 Create→Modify
  3. 文件日志未实现

---

## 阶段二：冷启动验证（§4.5）

### 2026-07-08 — 陌生 agent 冷启动试跑

- **操作**：派发全新 general subagent（无先前上下文），仅提供 SPEC.md + PLAN.md
- **指定任务**：Task 2（Data Models）和 Task 5（Parser）
- **subagent 行为**：
  - 暂停提问 2 个问题：①Task 1 依赖未满足 ②pytest 未安装
  - 无 spec 缺陷暴露
  - 12/12 测试通过，3 次 commit
- **commit**：`821a4a0`（scaffolding）、`bf4899f`（models）、`715711c`（parser）
- **结论**：SPEC 和 PLAN 质量足够高，陌生 agent 可仅凭文档无歧义实现
- **记录到**：SPEC_PROCESS.md（commit `b1686a5`）

---

## 阶段三：Subagent 驱动实现

### 2026-07-08 — Task 3: Config Loading

- **技能**：`subagent-driven-development`
- **subagent**：general（全新 session）
- **prompt 配置**：提供 PLAN.md Task 3 路径，要求严格按 TDD
- **输出**：harness/config.py + tests/test_config.py，3 测试通过
- **commit**：`dc6fb20`
- **人工干预**：无

### 2026-07-08 — Task 4: LLM Abstraction + Mock

- **subagent**：general
- **输出**：harness/llm/base.py（LLMProvider ABC + LLMError）、harness/llm/mock.py（MockLLM）、修改 llm/__init__.py
- **commit**：`f93e962`
- **测试**：4 测试通过，19 全量通过
- **人工干预**：无

### 2026-07-08 — Task 6: Tool Registry + File Tools

- **subagent**：general
- **输出**：harness/tools/__init__.py（ToolRegistry）、harness/tools/file_tools.py（read_file, write_file）
- **commit**：`82e5f6d`
- **测试**：6 测试通过，25 全量通过
- **人工干预**：无

### 2026-07-08 — Task 7: Shell Tool

- **subagent**：general
- **输出**：harness/tools/shell.py（run_shell with timeout）
- **commit**：`f0cb0af`
- **测试**：9 测试通过，28 全量通过
- **人工干预**：subagent 发现 PLAN 中 2 个 Windows 兼容性问题：
  1. `python -c '...'` 单引号在 Windows cmd.exe 不生效 → 改双引号
  2. 测试断言 "timeout" 与实现 "timed out" 不匹配 → 对齐断言
- **教训**：PLAN 中的测试代码在 Windows 上可能需要调整引号和断言文本

### 2026-07-08 — Task 8: Governance

- **subagent**：general
- **输出**：harness/governance.py（Governance 类：黑名单、路径限制、auto_deny）
- **commit**：`9e246af`
- **测试**：6 测试通过，34 全量通过
- **人工干预**：无

### 2026-07-08 — Task 9: Feedback

- **subagent**：general
- **输出**：harness/feedback.py（collect 函数：exit_code→pass/fail 判定）
- **commit**：`91b7739`
- **测试**：5 测试通过，39 全量通过
- **人工干预**：无

### 2026-07-08 — Task 10: Memory

- **subagent**：general
- **输出**：harness/memory.py（Memory 类：build_context, append, save_session, load_session）
- **commit**：`869423c`
- **测试**：4 测试通过，43 全量通过
- **人工干预**：无

### 2026-07-08 — Task 11: Agent Main Loop

- **subagent**：general
- **输出**：harness/loop.py（AgentLoop 类：六步主循环）
- **commit**：`14744ce`
- **测试**：4 测试通过，47 全量通过
- **人工干预**：无

### 2026-07-08 — Task 12: CLI + Keyring

- **subagent**：general
- **输出**：harness/cli.py（main, keyring_setup/status/clear, cmd_run）
- **commit**：`35d05c5`
- **测试**：4 测试通过，51 全量通过
- **人工干预**：subagent 发现 PLAN 中 logging 顺序 bug（FileHandler 在 makedirs 之前），已修复

### 2026-07-08 — Task 13: OpenAI Provider

- **subagent**：general
- **输出**：harness/llm/openai.py（OpenAILLM 类）
- **commit**：`d4f7f2b`
- **测试**：3 测试通过，54 全量通过
- **人工干预**：无

### 2026-07-08 — Task 14: Mechanism Demonstration (A.6)

- **subagent**：general
- **输出**：tests/test_demo.py（3 项机制演示）
- **commit**：`23b4708`
- **测试**：3 演示测试通过，57 全量通过
- **人工干预**：无

### 2026-07-08 — Task 15: Docker + PyPI

- **subagent**：general
- **输出**：Dockerfile + README.md
- **commit**：`6015f02`
- **人工干预**：subagent 发现 pyproject.toml build-backend 无效，改为 `setuptools.build_meta`

### 2026-07-08 — Task 16: CI Config

- **subagent**：general
- **输出**：.gitlab-ci.yml（unit-test + docker-build jobs）
- **commit**：`63be0bb`
- **测试**：57 全量通过
- **人工干预**：无

---

## 阶段四：最终评审与修复

### 2026-07-08 — 最终代码评审

- **技能**：`requesting-code-review`
- **subagent**：general（最终评审 agent）
- **评审结果**：可以合并到 master ✅
- **发现 1 Critical + 5 Important + 10 Minor**

### 2026-07-08 — 修复 Critical + Important

- **subagent**：general（fix subagent）
- **修复 3 个问题**：
  1. C1: loop.py 加 LLMError 重试（3 次指数退避）
  2. I1: governance.py 路径限制改用 commonpath
  3. I4: config.py 返回 deepcopy(DEFAULTS)
- **新增 4 个测试**：LLM 重试×2、路径绕过、config 不共享
- **commit**：`0c28f3b`
- **测试**：61 全量通过

### 2026-07-08 — 合并到 master

- dev 分支 fast-forward 合并到 master
- dev 分支删除

---

## 阶段五：真实 LLM 验证

### 2026-07-08 — DeepSeek API 接入

- **操作**：添加 base_url 配置支持，config.yaml 改为 deepseek
- **commit**：`5e86679`
- **修复**：memory.py 中 tool 结果消息 role 从 "tool" 改为 "user"（DeepSeek 要求 tool_call_id）
- **commit**：`d252769`

### 2026-07-08 — 本地试跑验证

- **任务 1**："读取 demo_bug.py，找出语法错误并修复"
- **结果**：7 轮循环完成，agent 读取→运行发现 SyntaxError→修复→验证通过
- **任务 2**：在另一个文件夹（harness-demo）运行
- **结果**：4 轮循环完成，agent 修复 fibonacci 边界 bug

### 2026-07-10 — 系统提示词平台感知

- **问题**：LLM 不知道在 Windows 上，使用 Linux 命令导致失败
- **修复**：系统提示词动态加入 `platform.system()` 和 `os.getcwd()`
- **commit**：`74f8acb`

---

## 阶段六：TUI 终端界面

### 2026-07-26 — TUI 开发

- **操作**：新增 `harness/tui.py`（rich 库回调渲染器），修改 `harness/loop.py` 加 callback 参数，修改 `harness/cli.py` 接入 TUI
- **commit**：`20cf984`
- **测试**：用真实 DeepSeek LLM 验证，5 轮完成 bug 修复，TUI 实时显示 Task/Turn/Action/Result/Complete 面板
- **人工干预**：无

---

## 阶段七：Phase 2 反馈闭环深化

### 2026-07-26 — Phase 2 brainstorming

- **技能**：`brainstorming`
- **操作**：审阅 Phase 1 完成情况，确定 Phase 2 方向为反馈闭环深化
- **方案选择**：用户选方案 C（完整闭环：流水线 + 自修正 + 模式检测）
- **设计文档**：`docs/superpowers/specs/2026-07-26-phase2-feedback-loop-design.md`（commit `957b5c3`）
- **设计修复**：发现 4 个问题（自修正概念混淆、模式分析读错字段、与 SPEC 不对齐、未提及更新 SPEC），全部修复（commit `270ed9d`）

### 2026-07-26 — Phase 2 writing-plans

- **技能**：`writing-plans`
- **操作**：将设计分解为 8 个 TDD task
- **计划文档**：`docs/superpowers/plans/2026-07-26-phase2-feedback-loop.md`（commit `0014dba`）

### 2026-07-26 — Phase 2 subagent-driven-development

- **技能**：`subagent-driven-development`
- **8 个 Task 全部完成**：

| Task | 内容 | Commit | 评审 |
|------|------|--------|------|
| 1 | 数据模型扩展（CheckResult, Feedback.checks, ActionResult.metadata） | `365ab55` | clean |
| 2 | 工具返回 metadata（path, tool name） | `54dbfe1` | clean |
| 3 | 语法检查阶段（py_compile） | `645db28` | clean |
| 4 | 模式分析阶段（3 次连续失败检测） | `addc632` | clean |
| 5 | 流水线集成（basic → syntax → pattern） | `7cbb8be` | clean |
| 6 | Memory 新增 append_hint() / get_history() | `43d4e62` | clean |
| 7 | Loop 注入 hint 驱动 LLM 自修正 | `5525067` | fix 后 clean |
| 8 | A.6 demo 第 4 项 + SPEC §3.6/§11.6 更新 | `8e94061` | clean |

- **Task 7 修复**：Windows 路径 JSON 转义 bug + 模式建议测试覆盖不足，fix subagent 修复
- **人工干预**：Task 7 中断后重新派发，发现 Windows 路径在 JSON 中需用 `json.dumps()` 转义

### 2026-07-26 — Phase 2 最终评审

- **技能**：`requesting-code-review`
- **评审结果**：Approved for merge
- **发现 2 个 Important**：
  1. hint 顺序在 LLM 上下文中颠倒（hint 在 action/result 之前）
  2. 模式分析未检查连续性（SPEC 说"连续失败"但代码只计数总数）
- **修复**：reorder hint injection + enforce consecutive check（commit `ef64d7f`）
- **新增 1 个测试**：`test_pattern_analysis_non_consecutive_no_suggestion`
- **测试**：88 全量通过

### 2026-07-26 — Phase 2 推送

- **技能**：`finishing-a-development-branch`
- **操作**：`git push origin master`（`20cf984`..`ef64d7f`）

---

## 教训总结

1. **PLAN 中的代码在 Windows 上可能需要调整**：引号语法、命令兼容性、断言文本匹配
2. **系统提示词必须包含运行环境信息**：否则 LLM 默认用 Linux 命令
3. **OpenAI 兼容 API 的 tool 消息格式**：不用 function calling 时，tool 结果应作为 user 消息
4. **logging 初始化顺序**：FileHandler 需要目录先存在
5. **pyproject.toml build-backend**：必须用有效的 `setuptools.build_meta`
6. **冷启动验证价值巨大**：证明了 SPEC/PLAN 质量足够高，但也暴露了"只选 2 个 task 不含依赖"的操作问题
7. **Windows 路径在 JSON 中需转义**：`json.dumps(str(path))` 而非直接插值，否则 `\U`、`\b` 等导致 JSON 解析失败
8. **设计文档中的"自修正"概念需澄清**：harness 不能自己修复文件，只能注入 hint 让 LLM 下轮自修正——这是"增强反馈"而非"自动修复"
9. **模式分析需检查连续性**：只计数总数会产生误报，必须检查最近 N 条是否全部失败
10. **hint 顺序影响 LLM 理解**：hint 应在 action/result 之后注入，LLM 才能理解 hint 指的是什么

# SPEC.md — harness-agent

> *Spec-Driven, Subagent-Built, Human-Owned.*

## 一、问题陈述

### 要解决什么问题

当 LLM 能完成大部分编码工作时，一个工程师的真正价值落在 **harness** 这层工程——把一个只会产生设想的 LLM，封装成一台能稳定、可靠工作的系统。本项目构建一个面向 Python 项目的 CLI coding agent harness，回答：决策、工具、治理、反馈、记忆、配置这些工程环节，到底需要什么？

### 目标用户

Python 开发者，希望用 AI 辅助完成编码任务（修 bug、加功能、重构），同时需要可控的治理护栏与确定性反馈。

### 为什么值得做

1. 市面上的 AI coding 工具多为黑盒，开发者无法理解其底层机制。本项目让开发者亲手构建 harness 内核，理解 agent 底层到底在做什么。
2. 反馈不是靠提示词让 LLM 自查，而是真正跑 pytest/lint 得到确定性结果再回灌——这是"机制是代码"的典型实践。
3. 治理护栏是代码拦截，不是一句"请小心"——移除 LLM 后仍可确定性测试。

---

## 二、用户故事

遵循 INVEST 原则（Independent / Negotiable / Valuable / Estimable / Small / Testable）：

1. **US-1 修复 Bug**：作为 Python 开发者，我想用自然语言描述任务，让 agent 自动读写代码并运行测试修复 bug，以便节省调试时间。
2. **US-2 危险命令拦截**：作为 Python 开发者，我想 agent 在执行危险命令（如 `rm -rf`）前暂停并请求确认，以便防止误操作破坏环境。
3. **US-3 测试反馈自修正**：作为 Python 开发者，我想 agent 运行测试后自动根据失败结果修正代码，以便快速迭代直到测试通过。
4. **US-4 凭据安全**：作为 Python 开发者，我想 API key 安全存储在操作系统钥匙串中，并能查看状态/更新/清除，以便保护凭据不被泄露。
5. **US-5 一键部署**：作为 Python 开发者，我想通过 Docker 或 pip 一键安装运行 agent，以便在新机器上快速部署。
6. **US-6 跨会话记忆**：作为 Python 开发者，我想 agent 记住跨会话的项目上下文和历史决策，以便延续之前的工作而非从零开始。

---

## 三、功能规约

按模块拆分，每项描述输入 / 行为 / 输出 / 边界条件 / 错误处理。

### 3.1 决策模块 (`harness/loop.py`)

- **输入**：用户任务描述（str）、配置（Config）、LLMProvider 实例
- **行为**：执行主循环——上下文组装 → 调用 LLM → 解析响应为 Action → 治理检查 → 工具分发执行 → 反馈收集 → 记忆追加 → 停机判断
- **输出**：任务执行结果（成功/失败 + 摘要）
- **边界条件**：最大轮数（默认 20）；解析失败重试上限（3 次）
- **错误处理**：
  - 解析失败 → 回灌"格式错误，请返回 JSON" → LLM 重试（超限停机）
  - 工具异常 → 捕获异常 → 生成 failed Feedback → 回灌给 LLM
  - Governance 拒绝 → 回灌拒绝原因 → LLM 选择替代方案或停机
  - Governance 需确认 → 交互模式 input() 确认；CI 模式（auto_deny=true）自动拒绝

### 3.2 解析器模块 (`harness/parser.py`)

- **输入**：LLM 响应文本（str）
- **行为**：解析 JSON 格式响应为 Action 对象；识别 `task_complete` 信号
- **输出**：Action 对象（`tool="task_complete"` 时表示停机，loop 检测后终止循环）
- **LLM 响应格式契约**：
  ```json
  {"tool": "write_file", "args": {"path": "foo.py", "content": "..."}}
  {"tool": "task_complete", "args": {"summary": "已修复 bug"}}
  ```
- **边界条件**：响应可能包含非 JSON 文本（LLM 解释 + JSON 动作）。parser 使用正则提取最后一个 JSON 对象（`{.*}` 贪婪匹配），提取失败则视为解析错误。
- **错误处理**：JSON 解析失败 → 返回 ParseError，loop 回灌错误让 LLM 重试

### 3.3 LLM 抽象层 (`harness/llm/`)

- **输入**：Conversation（List[Message]）
- **行为**：调用供应商 API 获取响应
- **输出**：响应文本（str）
- **接口**：`LLMProvider.complete(messages: List[Message]) -> str`
- **实现**：
  - `llm/openai.py`：OpenAI Chat Completions API（支持 OpenAI 及 DeepSeek 等兼容 API，通过 `base_url` 配置）
  - `llm/mock.py`：确定性响应（单测用，按预设脚本返回）
- **边界条件**：API 限流、网络错误、无效 key
- **错误处理**：API 异常 → 抛出 LLMError，loop 捕获后重试（最多 3 次，指数退避），超限则停机并报错
- **扩展方式**：新增 OpenAI 兼容供应商只需在 config.yaml 设置 `provider`、`model`、`base_url`

### 3.4 工具模块 (`harness/tools/`)

- **输入**：Action（tool 名称 + args）
- **行为**：通过 ToolRegistry 分发到对应工具函数执行
- **输出**：ActionResult
- **工具清单**：
  - `read_file(path: str) -> ActionResult`：读取文件内容
  - `write_file(path: str, content: str) -> ActionResult`：写入文件
  - `run_shell(command: str) -> ActionResult`：执行 shell 命令
- **注册机制**：`ToolRegistry.register(name, func)` + `ToolRegistry.dispatch(action)`
- **边界条件**：文件不存在、权限不足、命令超时（默认 30 秒，可配置）
- **错误处理**：捕获异常 → ActionResult(success=False, error=异常信息)；命令超时 → 终止子进程，返回 ActionResult(success=False, error="timeout")

### 3.5 治理模块 (`harness/governance.py`)

- **输入**：Action
- **行为**：检查动作是否危险，返回 Allow / Deny / Confirm
- **输出**：GovernanceDecision(allow: bool, confirm: bool, reason: str)
- **黑名单**（配置项 `governance.blocked_commands`）：
  - `rm -rf`：删除目录树
  - `git push --force`：强制推送
  - `curl` / `wget`：外部网络请求
  - `chmod 777`：危险权限
  - `sudo`：提权操作
- **边界条件**：非 shell 类动作（read_file/write_file）默认 Allow；write_file 限制在当前工作目录及子目录内（防止写系统文件）
- **错误处理**：精确匹配黑名单 → Deny + 原因；命令包含黑名单模式作为子串 → Confirm + 原因；write_file 路径超出项目目录 → Deny + 原因；其余 → Allow
- **CI 模式**：`governance.auto_deny=true` 时 Confirm 自动转为 Deny

### 3.6 反馈模块 (`harness/feedback.py`)

- **输入**：ActionResult、工具名、轮次号、历史记录
- **行为**：执行多阶段反馈流水线——基础检查 → 语法检查（写 .py 文件后自动 py_compile）→ 模式分析（检测连续失败模式）
- **输出**：Feedback(passed, summary, raw_result, checks[], suggested_next_action, turn_number)
- **流水线阶段**：
  1. 基础检查：`result.success` → PASS/FAIL
  2. 语法检查：`write_file` 写 `.py` 文件后自动运行 `py_compile`，失败则 `passed=False`
  3. 模式分析：检测最近 5 轮中是否有 3 次以上连续失败，生成建议
- **边界条件**：非 `.py` 文件跳过语法检查；历史不足 3 轮不生成建议
- **错误处理**：语法检查失败 → `CheckResult(passed=False, detail=错误信息)` → 注入 hint 到 LLM 上下文
- **自修正机制**：harness 检测失败 → 注入结构化 hint → LLM 下轮看到 hint → 自修正。harness 不直接修复文件（那需要 LLM 智能）。

### 3.7 记忆模块 (`harness/memory.py`)

- **输入**：用户任务、对话历史、工具执行结果
- **行为**：组装上下文供 LLM 使用；管理会话内历史；跨会话持久化
- **输出**：List[Message]（供 LLM 调用）
- **会话内**：维护对话历史（系统提示 + 用户任务 + 每轮 Action/Feedback）
- **跨会话**：将会话摘要写入 `.harness/sessions/<session_id>.json`；下次启动可加载
- **Session 结构**：`Session(id, task, history: List[Tuple[Action, Feedback]], summary: str)`
- **边界条件**：对话过长超出 token 限制
- **错误处理**：超长时截断最早的非系统消息；MVP 设 max_turns 间接限制
- **MVP 范围**：全量载入对话历史。"按需提供给 LLM 而非全量载入"为阶段 2 内容。

### 3.8 配置模块 (`harness/config.py`)

- **输入**：YAML 配置文件路径
- **行为**：加载配置，提供默认值
- **输出**：Config 对象
- **配置 schema**：
  ```yaml
  llm:
    provider: deepseek       # openai / deepseek / mock
    model: deepseek-chat     # deepseek-chat / gpt-4o / etc.
    base_url: "https://api.deepseek.com"  # omit for OpenAI, required for DeepSeek
  max_turns: 20
  governance:
    blocked_commands:
      - "rm -rf"
      - "git push --force"
      - "curl"
      - "wget"
      - "chmod 777"
      - "sudo"
    auto_deny: false         # CI 模式设 true
  session:
    dir: ".harness/sessions"
  logging:
    level: info
    dir: ".harness/logs"
  ```
- **边界条件**：配置文件不存在 → 使用默认值；字段缺失 → 使用字段默认值
- **错误处理**：YAML 解析失败 → 抛出 ConfigError

### 3.9 CLI 模块 (`harness/cli.py`)

- **输入**：命令行参数
- **行为**：解析子命令，分发到对应处理函数
- **子命令**：
  - `harness run "task"`：运行 agent
  - `harness keyring setup`：引导录入 API key（隐藏输入）；若已存在则覆盖更新
  - `harness keyring status`：显示已配置供应商（不回显明文）
  - `harness keyring clear`：清除 key
- **输出**：执行结果或状态信息
- **边界条件**：未配置 key 时运行 `harness run` → 提示先执行 `keyring setup`
- **错误处理**：参数缺失 → 显示用法；未知子命令 → 报错

### 3.10 日志模块（集成于各模块）

- **行为**：Python logging，输出到 stderr + `.harness/logs/` 文件
- **记录内容**：每轮决策/动作/结果、治理拦截、反馈回灌
- **格式**：`[turn N] action=tool(args) → success=bool`

---

## 四、非功能性需求

### 4.1 性能

- 单轮 LLM 调用 + 工具执行延迟 < 30 秒（取决于 LLM 供应商）
- 本地工具执行（read_file/write_file/run_shell）< 5 秒
- max_turns 默认 20 轮，防止无限循环

### 4.2 安全（含凭据威胁模型）

**凭据威胁模型**：

| 威胁 | 对策 |
|------|------|
| key 硬编码进源码 | 禁止；CI 检查 |
| key 提交进 Git | .gitignore 排除 .env；pre-commit 检查 |
| key 写入日志 | 日志中 key 相关字段脱敏 |
| key 写入终端 history | 不使用命令行 export；用 keyring 存储 |
| .env 明文风险 | keyring 为主方案；.env 仅作备选并说明风险 |
| 进程环境可见 | keyring 方案不经过环境变量 |

**凭据存储方案**：
- 使用 `keyring` 库（跨平台：Windows Credential Manager / macOS Keychain / Linux Secret Service）
- 首次运行 `harness keyring setup` 引导录入（隐藏输入，getpass）
- `harness keyring status` 显示已配置供应商名称，不回显明文
- `harness keyring clear` 清除指定或全部 key

### 4.3 可用性

- CLI 交互式引导首次配置
- 错误信息清晰可操作（不只是 traceback）
- README 提供完整安装和运行指南

### 4.4 可观测性

- 每轮决策/动作/结果记录到 `.harness/logs/`
- 治理拦截事件记录
- 反馈回灌事件记录
- 日志级别可配置（debug/info/warning/error）

---

## 五、系统架构

### 5.1 组件图

```
┌──────────────────────────────────────────────────────────┐
│                        CLI (cli.py)                       │
│            harness run "task" / keyring subcommands       │
│                         + TUI (tui.py)                    │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│                  Agent 主循环 (loop.py)                     │
│                                                           │
│   while not done:                                         │
│     1. context = memory.build_context()                  │
│     2. response = llm.complete(context)                  │
│     3. action = parser.parse(response)                   │
│     4. decision = governance.check(action)               │
│        if blocked: result = blocked_feedback              │
│        elif confirm: result = hitl_or_auto()              │
│        else: result = tools.dispatch(action)              │
│     5. feedback = collect(result, tool, turn, history)    │
│        → pipeline: basic → syntax check → pattern        │
│     6. memory.append(action, feedback)                    │
│     7. if feedback has failed checks or suggestion:      │
│          memory.append_hint(detail)  ← drives LLM fix     │
│     8. done = (action.tool == "task_complete")           │
└──┬──────┬──────┬──────┬──────┬───────────────────────────┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────────┐
│ LLM  ││ 工具  ││ 治理  ││ 反馈  ││ 记忆+配置 │
│抽象层 ││ 分发  ││ 护栏  ││ 流水线 ││ + hint   │
└──┬───┘└──────┘└──────┘└──────┘└──────────┘
   │
   ├─── llm/openai.py   (OpenAI + DeepSeek via base_url)
   └─── llm/mock.py     (确定性测试用)
```

### 5.2 数据流

```
用户输入任务
    │
    ▼
Memory.build_context() ──→ List[Message]
    │
    ▼
LLMProvider.complete() ──→ str (LLM 响应)
    │
    ▼
Parser.parse() ──→ Action
    │
    ├─ Action.tool == "task_complete" → 循环结束
    │
    ▼
Governance.check(Action) ──→ GovernanceDecision
    │
    ├─ Deny → ActionResult(success=False) → 进入反馈流水线
    ├─ Confirm → HITL input() / auto_deny → 进入反馈流水线
    │
    ▼ Allow
ToolRegistry.dispatch(Action) ──→ ActionResult (含 metadata)
    │
    ▼
Feedback.collect(result, tool, turn, history) ──→ Feedback
    │  ┌─ Stage 1: 基础检查 (success/exit_code → PASS/FAIL)
    │  ├─ Stage 2: 语法检查 (write_file .py → py_compile)
    │  └─ Stage 3: 模式分析 (3 次连续失败 → suggestion)
    │
    ▼
Memory.append(Action, Feedback) → 更新对话历史
    │
    ├─ Feedback 有 failed checks → Memory.append_hint(错误详情)
    ├─ Feedback 有 suggestion → Memory.append_hint(建议)
    │
    ▼
回到循环顶部 (LLM 下轮看到 [Tool Result] + [Hint] → 自修正)
```

### 5.3 外部依赖

| 依赖 | 类型 | 用途 |
|------|------|------|
| OpenAI API | LLM 供应商 | GPT-4o 等模型调用 |
| DeepSeek API | LLM 供应商 | DeepSeek 模型调用（via base_url） |
| `keyring` | Python 库 | 跨平台凭据安全存储 |
| `pytest` | Python 库 | 测试框架 |
| `pyyaml` | Python 库 | YAML 配置解析 |
| `rich` | Python 库 | TUI 终端界面渲染 |
| Docker | 分发工具 | 容器镜像构建 |
| PyPI | 分发平台 | pip 包发布 |

---

## 六、数据模型

### 6.1 核心实体

```python
@dataclass
class Message:
    role: str           # "system" / "user" / "assistant"
    content: str        # 消息内容

@dataclass
class Conversation:
    messages: List[Message]

@dataclass
class Action:
    tool: str           # "read_file" / "write_file" / "run_shell" / "task_complete"
    args: dict          # 工具参数
    raw: str            # LLM 原始输出（调试用）

@dataclass
class ActionResult:
    success: bool       # 客观判定（exit_code == 0 或无异常）
    output: str         # stdout
    error: str          # stderr / 异常信息
    exit_code: int      # shell 退出码（非 shell 工具为 0/-1）
    metadata: dict = field(default_factory=dict)  # 工具元数据（path, tool name 等）

@dataclass
class CheckResult:
    name: str           # "syntax" / "pattern"
    passed: bool
    detail: str         # 检查详情

@dataclass
class Feedback:
    passed: bool        # 客观判定结果
    summary: str        # 结构化摘要（回灌给 LLM）
    raw_result: ActionResult
    checks: List[CheckResult] = field(default_factory=list)  # 流水线检查结果
    suggested_next_action: str = ""  # 模式分析建议
    turn_number: int = 0  # 轮次号

@dataclass
class GovernanceDecision:
    allow: bool         # 是否允许执行
    confirm: bool       # 是否需要人工确认
    reason: str         # 决策原因

@dataclass
class Session:
    id: str             # 会话 ID（时间戳生成）
    task: str           # 用户任务描述
    history: List[Tuple[Action, Feedback]]  # 执行历史（动作+反馈配对）
    summary: str        # 会话摘要

@dataclass
class Config:
    llm_provider: str
    llm_model: str
    llm_base_url: str   # OpenAI 兼容 API 的 base_url（DeepSeek 等）
    max_turns: int
    blocked_commands: List[str]
    auto_deny: bool
    session_dir: str
    log_level: str
    log_dir: str
```

### 6.2 关系

```
Config ──配置──→ Loop
Loop ──调用──→ LLMProvider (抽象)
LLMProvider <──实现── OpenAI(+DeepSeek)/Mock
Loop ──调用──→ Parser
Loop ──调用──→ Governance
Loop ──调用──→ ToolRegistry
ToolRegistry ──分发──→ read_file/write_file/run_shell
Loop ──调用──→ Feedback (多阶段流水线)
Loop ──调用──→ Memory (含 append_hint / get_history)
Memory ──持久化──→ Session (JSON 文件)
CLI ──启动──→ Loop + Config + LLMProvider + TUI
TUI ──回调──→ Loop (on_start/on_turn/on_action/on_result/on_complete)
```

### 6.3 约束

- Action.tool 必须在 ToolRegistry 中已注册（否则 ActionResult(success=False)）
- GovernanceDecision.allow 和 confirm 不能同时为 True
- Session.id 全局唯一（时间戳 + 随机后缀）
- Config.max_turns >= 1

---

## 七、凭据与分发设计

### 7.1 Key 存储方案

- **存储**：`keyring` 库，服务名 `harness-agent`，按供应商名存储（`openai` / `deepseek`）
- **录入流程**：
  1. 用户执行 `harness keyring setup`
  2. CLI 提示选择供应商
  3. 使用 `getpass.getpass()` 隐藏输入 key
  4. 调用 `keyring.set_password("harness-agent", provider, key)`
  5. 确认存储成功
- **查看流程**：
  1. 用户执行 `harness keyring status`
  2. 遍历已知供应商，检查 `keyring.get_password()` 是否非空
  3. 输出：`openai: 已配置` / `deepseek: 未配置`（不回显明文）
- **清除流程**：
  1. 用户执行 `harness keyring clear [--provider openai]`
  2. 调用 `keyring.delete_password()`
  3. 确认清除成功

### 7.2 分发设计

**Docker 镜像**：
- `Dockerfile`：基于 `python:3.12-slim`，安装依赖，复制源码
- 构建：`docker build -t harness-agent .`
- 运行：`docker run -it --rm -v $(pwd):/workspace harness-agent run "task"`
- Key 配置：容器内无法访问宿主机 keyring，改用环境变量传入（`docker run -e OPENAI_API_KEY=...`）。代码中优先读 keyring，回退到环境变量。README 注明环境变量方案的明文风险。

**PyPI 包**：
- `pyproject.toml` 配置包名 `harness-agent`
- 安装：`pip install harness-agent`
- 运行：`harness run "task"`
- Key 配置：安装后执行 `harness keyring setup`

### 7.3 目标平台

- Docker：Linux / macOS / Windows（Docker Desktop）
- PyPI：Python 3.10+，Linux / macOS / Windows

---

## 八、技术选型与理由

| 选型 | 理由 |
|------|------|
| **Python** | LLM 生态最成熟；pytest 测试框架完善；课程 AI 方向默认语言 |
| **可插拔 LLM** | 不绑定单一供应商；Mock 实现满足 A.4-C 离线测试要求 |
| **keyring 库** | 跨平台支持 Windows Credential Manager / macOS Keychain / Linux Secret Service，满足 §3.1 安全存储要求 |
| **pytest** | Python 标准测试框架；支持 fixture/mock；满足 §4.8 一键测试要求 |
| **Docker + PyPI** | Docker 满足"全新机器从零运行"检验；PyPI 满足开发者习惯 |
| **YAML 配置** | 声明式规则约束 agent 行为（A.1 配置维度）；人类可读可编辑 |
| **不使用 LangChain/AutoGen 等** | A.4-A 要求自实现 harness 内核，不寄生现成框架 |

---

## 九、验收标准

| 功能 | 完成的客观判定标准 |
|------|-------------------|
| Agent 主循环 | Mock LLM 驱动下完成一轮"调用→解析→执行→回灌→停机"，单测通过 |
| LLM 抽象层 | Mock provider 返回确定性响应；OpenAI provider 可真实调用（手动验证） |
| 解析器 | 给定 JSON 格式 LLM 响应，正确解析为 Action；给定 task_complete，正确识别停机 |
| 工具 | read_file 读取文件返回内容；write_file 写入文件后 read_file 可读回；run_shell 执行命令返回 stdout/exit_code |
| 治理 | `governance.check(Action(command="rm -rf /"))` 返回 Deny；安全命令返回 Allow |
| 反馈 | exit_code=0 → Feedback(passed=True)；exit_code=1 → Feedback(passed=False, summary 含错误信息) |
| 记忆 | 会话内历史正确追加；Session 写入 .harness/sessions/ 后可重新加载 |
| 配置 | YAML 文件加载为 Config 对象；缺失字段使用默认值 |
| CLI | `harness run "task"` 启动 agent；`harness keyring setup/status/clear` 正常工作 |
| 凭据 | key 存入 keyring 后 status 显示"已配置"；clear 后显示"未配置"；日志中无明文 key |
| 分发 | `docker build` + `docker run` 成功；`pip install` 后 `harness` 命令可用 |
| 测试 | `pytest tests/` 全部通过；CI 中 unit-test job pass |
| 机制演示 | ① 治理拦截危险动作；② 注入失败反馈改变 LLM 下一步；③ 反馈闭环确定性行为；④ 反馈流水线语法检查（写文件后自动 py_compile，失败注入 hint 驱动 LLM 自修正）。形式：pytest 测试用例（`tests/test_demo.py`），在 mock LLM 下确定性运行，可通过 `pytest tests/test_demo.py -v` 一键复现 |

---

## 十、风险与未决问题

| # | 风险 | 影响 | 缓解 |
|---|------|------|------|
| 1 | LLM 返回非 JSON 格式 | 解析失败，循环卡住 | 解析失败重试 3 次后停机；系统提示明确要求 JSON 格式 |
| 2 | LLM 不遵循工具格式 | 调用不存在的工具 | ToolRegistry 返回 ActionResult(success=False)；回灌错误让 LLM 重试 |
| 3 | 对话历史超长 | 超出 token 限制 | max_turns 间接限制；超长时截断最早非系统消息 |
| 4 | shell 命令注入 | 安全风险 | governance 黑名单拦截；MVP 不做沙箱（阶段 2 考虑） |
| 5 | keyring 在 CI 环境不可用 | 无法存储 key | CI 使用 mock LLM，不需要真实 key |
| 6 | 不同 LLM 供应商响应格式差异 | 解析器需适配 | 统一要求 JSON 格式输出；parser 只解析 JSON |
| 7 | Mock LLM 脚本维护成本 | 测试用例编写量 | 按场景编写脚本：正常流程/解析失败/治理拦截/反馈修正 |

---

## 十一、领域与机制设计（A.5 额外要求）

### 11.1 领域：Coding（Python 项目）

本 harness 面向 Python 项目的编码场景：读写 Python 代码、执行 shell 命令、运行 pytest/lint/typecheck。

### 11.2 反馈信号

- **MVP（已实现）**：捕获工具执行结果（stdout/stderr/exit_code），解析 exit_code 做客观判定（0=pass，非0=fail），生成结构化摘要回灌给循环。
- **阶段 2 深化（已实现）**：多阶段反馈流水线（基础检查 → 语法检查 py_compile → 模式分析），`CheckResult` 结构化检查结果，失败时注入 `[Hint]` 驱动 LLM 自修正。
- **阶段 2 深化（未实现，YAGNI 裁剪）**：typecheck（mypy）、coverage、失败分类（语法/类型/逻辑/风格）。增加复杂度但价值有限，留作未来工作。
- **编码实现**：`feedback.py` 中的 `collect(result, tool, turn_number, history) -> Feedback` 函数。注入假 ActionResult 即可确定性测试，无需真实 LLM。

### 11.3 危险动作

- **MVP（已实现）**：黑名单拦截（`rm -rf` / `git push --force` / `curl` / `wget` / `chmod 777` / `sudo`）+ 路径围栏（write_file 限制在项目目录内）+ auto_deny（CI 模式）。`governance.check(action) -> GovernanceDecision` 函数。
- **阶段 2 深化（未实现，YAGNI 裁剪）**：HITL 状态机（待确认→已确认/已拒绝）、风险分级（safe/needs-confirm/blocked）。MVP 的 Allow/Confirm/Deny 三态已满足需求。
- **编码实现**：`governance.py` 中的 `check(action: Action) -> GovernanceDecision` 函数。构造 `Action(command="rm -rf /")` 直接测试，每次都返回 Deny。

### 11.4 所需工具

- `read_file(path)`：读取文件内容
- `write_file(path, content)`：写入文件（返回含 `metadata` 供流水线使用）
- `run_shell(command)`：执行 shell 命令（含运行 pytest/lint/typecheck）
- **阶段 2（未实现，YAGNI 裁剪）**：`run_tests()`、`run_lint()`、`run_typecheck()` 专用工具。当前通过 `run_shell` 调用即可，无需单独封装。

### 11.5 记忆需求

- **MVP（已实现）**：会话内对话历史（系统提示 + 用户任务 + 每轮 Action/Feedback）；跨会话 Session 持久化（.harness/sessions/）。
- **阶段 2 深化（已实现）**：`Memory.append_hint()` 注入 LLM 可见提示；`Memory.get_history()` 返回近期历史供模式分析。
- **阶段 2 深化（未实现，YAGNI 裁剪）**：项目约定学习（从 pyproject.toml 提取测试命令等）；按需检索而非全量载入。留作未来工作。
- **编码实现**：`memory.py` 中的 `build_context()` / `append()` / `append_hint()` / `get_history()` / `save_session()` / `load_session()` 函数。直接测试，无需真实 LLM。

### 11.6 重点维度：反馈闭环

**选择理由**：
1. 反馈闭环是 coding agent 最核心的差异化能力——运行测试、得到结果、自我修正。
2. 天然由代码构成（校验器/传感器），最契合 A.4-B"机制必须是代码"要求。
3. 最容易用 mock 做确定性单测（注入假测试结果即可验证自修正逻辑）。
4. A.6 机制演示②（注入失败反馈改变 LLM 行为）直接依赖此维度。

**编码实现方式**：
- MVP：`Feedback.collect(ActionResult) -> Feedback`，解析 exit_code 做客观判定。
- 阶段 2（已实现）：多阶段反馈流水线（基础检查 → 语法检查 py_compile → 模式分析），`CheckResult` 结构化检查结果，`Feedback.checks[]` 存储所有检查结果，`suggested_next_action` 存储模式分析建议。Loop 在检测到失败时注入 `[Hint]` 消息到 LLM 上下文，驱动 LLM 自修正。
- 阶段 2（未实现，YAGNI 裁剪）：typecheck（mypy）、coverage、HITL 状态机、项目约定学习。这些增加复杂度但价值有限，留作未来工作。

---

## 十二、两阶段交付计划

### 阶段 1：MVP（最小可运行 Harness）— 已完成 ✅

- 六维度最低实现：决策（主循环）/ 工具（read/write/shell）/ 治理（黑名单）/ 反馈（exit_code 判定）/ 记忆（会话+持久化）/ 配置（YAML）
- LLM 抽象层：OpenAI + Mock；DeepSeek 通过 base_url 兼容接入
- CLI + keyring 凭据管理
- Docker + PyPI 分发
- mock-LLM 单元测试（61 个）
- 机制演示（3 项）
- TUI 终端界面（rich 库回调渲染）

### 阶段 2：反馈闭环深化 — 已完成 ✅

**已实现**：
- 多阶段反馈流水线（基础检查 → 语法检查 py_compile → 模式分析）
- `CheckResult` 结构化检查结果
- `Feedback.checks[]` / `suggested_next_action` / `turn_number`
- `ActionResult.metadata` 工具元数据
- `Memory.append_hint()` / `Memory.get_history()`
- Loop 注入 `[Hint]` 驱动 LLM 自修正
- 机制演示第 4 项（流水线语法检查 → hint → 自修正）
- 27 个新测试（共 88 个）

**未实现（YAGNI 裁剪）**：
- typecheck（mypy）、coverage — 增加复杂度但价值有限
- HITL 状态机、风险分级、范围围栏 — MVP 治理已满足需求
- 项目约定学习、按需检索 — 记忆深化留作未来工作
- Anthropic / Google provider — 可通过 base_url 扩展，无需单独实现

# 这个项目做了什么？大一学生可以学到什么？

> 本文写给想了解 AI4SE 期末项目的大一同学，不假设你有任何前置知识。

---

## 一、一句话说清楚项目

这个项目造了一个"AI 程序员的管理系统"。

你给这个系统一个任务，比如"修复 bug.py 里的语法错误"，它会：
1. 调用大模型（LLM，比如 DeepSeek）来决定"下一步做什么"
2. 执行读文件、写文件、跑命令等操作
3. 检查操作结果，判断是否完成
4. 如果出错，把错误信息反馈给大模型，让它自己修正
5. 重复直到任务完成或达到上限

整个过程不需要人盯着。这就是一个 **Coding Agent Harness**——让 AI 能自主完成编程任务的基础设施。

---

## 二、项目里有什么（按难度排序）

### 看得见的东西

- **命令行工具**：安装后输入 `harness run "修复 bug.py"` 就能跑
- **终端界面**：运行时会实时显示 AI 在想什么、在做什么
- **配置文件**：用 YAML 文件控制 AI 的行为（用哪个模型、最多跑多少轮、禁止哪些危险命令）

### 看不见但重要的东西（代码层面）

| 模块 | 作用 | 大一能理解的说法 |
|------|------|------------------|
| 主循环 (`loop.py`) | 决定"什么时候该做什么" | 像写了一个 while 循环，每次问 AI 下一步，然后执行，再问，直到结束 |
| 工具 (`tools/`) | 让 AI 能读写文件、跑命令 | 给 AI 装了一双手，让它能真正干活，不只是聊天 |
| 治理 (`governance.py`) | 拦截危险命令 | 像一个保安，AI 想执行 `rm -rf /` 的时候拦住它 |
| 反馈 (`feedback.py`) | 检查 AI 的产出是否正确 | 像一个质检员，语法错误、连续失败都能检测出来 |
| 记忆 (`memory.py`) | 让 AI 记住之前说过什么 | 像聊天记录的"历史消息"，还能跨会话保存 |
| 配置 (`config.py`) | 让用户能自定义行为 | 像游戏里的设置面板，不用改代码就能调参数 |

### 项目规模

- **24 个提交**，全部有规范的 commit message
- **88 个单元测试**，全部通过
- **2 个 CI 配置文件**（GitLab + GitHub Actions），每次推送自动跑测试
- **Docker 镜像**，一行命令就能部署
- **6 个交付文档**：SPEC（设计文档）、PLAN（实现计划）、SPEC_PROCESS（设计过程）、AGENT_LOG（开发日志）、README（使用说明）、REFLECTION（反思报告）

---

## 三、大一学生应该学什么

### 1. 模块化思维：把大问题拆成小零件

这个项目不是"写一个巨大的程序"，而是拆成了 12 个 Python 文件，每个文件只做一件事：
- `models.py` 只定义数据类型
- `parser.py` 只解析 AI 的回复
- `governance.py` 只负责安全检查
- 每个文件不超过 300 行

**你学到的**：写代码不是越短越好，而是越清晰越好。一个文件只做一件事，以后改起来才不头疼。

### 2. 测试驱动开发：先写测试，再写代码

这个项目全程是"先写一个会失败的测试 → 写代码让它通过 → 提交"。88 个测试覆盖了所有核心功能。

**你学到的**：测试不是"写完代码后补的作业"，而是"定义"什么是正确的代码。没有测试，你永远不知道改坏没改坏。

### 3. 安全是设计出来的，不是后加的

API key 不能用明文存、不能进 Git 历史、不能写进日志、不能出现在终端历史里。这些都是设计阶段就确定的，不是"后来发现有问题再补"。

**你学到的**：安全问题在写代码之前就要想清楚。等代码写完了再想安全，往往已经晚了。

### 4. 代码治理护栏：AI 再聪明也不能为所欲为

这个项目最核心的设计之一是"治理"——AI 想执行 `rm -rf /`、`curl`、`sudo` 这些危险命令时，系统会拦截，需要人工确认才能放行。

**你学到的**：给 AI 能力的时候，一定要同时给限制。不管 AI 多聪明，你都要先想好"如果它做坏事怎么办"。

### 5. 反馈闭环：让 AI 能从错误中学习

AI 写代码肯定会出错。这个项目不是"出错就停止"，而是把错误信息（编译错误、测试失败）反馈给 AI，让它自己修正。

**你学到的**：一个系统的价值不在于"一次做对"，而在于"做错了能自己修"。这个道理也适用于你自己的学习。

### 6. 文档是代码的一部分

6 个 md 文档不是"凑字数"，而是：
- SPEC 在你写代码之前就决定了"要做什么"
- PLAN 决定了"分几步做"
- AGENT_LOG 记录了"每一步发生了什么"
- REFLECTION 反思了"哪些做得好、哪些做得不好"

**你学到的**：代码只告诉你怎么实现，文档告诉别人（和未来的你）为什么这么实现。后者往往更重要。

### 7. 自动化测试和持续集成

每次推送代码，GitHub Actions 自动运行 88 个测试。如果测试失败，你会在第一时间知道，不用等到老师检查才发现。

**你学到的**：CI/CD 不是企业才用的东西。个人项目一样可以用，而且越早用越省心。

### 8. 凭据安全：不要硬编码任何秘密

API key 用系统密钥管理器（Windows Credential Manager / macOS Keychain）存储，而不是写在 `.env` 文件里。输入 key 的时候用 `getpass` 隐藏输入，不让屏幕和终端历史记录。

**你学到的**：重要的密码不要写在代码里，不要写在配置文件里，不要写在任何可能被 Git 记录的地方。

---

## 四、一些具体的代码技巧（可以直接用）

| 技巧 | 代码示例 | 学到了什么 |
|------|---------|-----------|
| 用 `getpass.getpass()` 隐藏输入 | `key = getpass.getpass("Enter API key: ")` | 密码输入时屏幕不显示，终端 history 也不记录 |
| 用 `Signal` 枚举表示状态 | `class TaskStatus(Enum): PENDING = "pending"` | 比用字符串更安全，写错会报错 |
| 用 `pathlib.Path` 处理路径 | `Path("config.yaml").read_text()` | 比 `os.path.join()` 更简洁，跨平台兼容 |
| 用 `pytest.fixture` 共享测试数据 | `@pytest.fixture def config(): return load_config(...)` | 测试代码不重复，改一处全改 |
| 用 `dataclass` 定义数据结构 | `@dataclass class Message: role: str; content: str` | 比 dict 更清晰，有类型提示 |
| 用 `rich` 做终端界面 | `panel = Panel(text, title="Thinking")` | 三行代码就能做出好看的终端 UI |

---

## 五、如果你想自己试试

```bash
# 克隆项目
git clone https://github.com/g-2007-code/harness-agent.git
cd harness-agent

# 安装
pip install -e ".[dev]"

# 跑测试（不需要任何 API key）
pytest tests/ -v

# 看看机制演示（不需要 API key）
pytest tests/test_demo.py -v

# 试试真实运行（需要 API key）
# 先配置 key
harness keyring setup
# 再运行
harness run "写一个 Python 函数，计算斐波那契数列的第 n 项"
```

---

## 六、总结

这个项目最重要的不是"写了一个能用的工具"，而是展示了一套**规范的软件开发流程**：

1. 先想清楚做什么（SPEC）
2. 再想清楚分几步做（PLAN）
3. 每一步先写测试再写代码（TDD）
4. 每步做完都提交、评审（commit + review）
5. 最后反思什么做得好、什么做得不好（REFLECTION）

这套流程不分项目大小，不分语言，大一就能开始用。你不需要等到"学够了"再开始规范地写代码。现在就可以。

> 关于 AI 辅助编程，这个项目最真实的结论是：AI 可以帮你写很多代码，但**决定写什么、为什么写、写得对不对**——这些还是人的事。

---

## 七、底层代码结构与原理（逐文件讲解）

这一节带你真正"打开"这个项目，看每个文件里的代码长什么样、为什么这么写。建议你打开项目代码边看边读。

### 项目文件总览

```
harness/                  # 核心代码
├── __init__.py           # 空文件，让 Python 把 harness 当包
├── models.py             # 数据类型定义
├── config.py             # 读配置文件
├── parser.py             # 解析 LLM 返回的 JSON
├── governance.py         # 安全检查
├── feedback.py           # 反馈流水线
├── memory.py             # 记忆管理
├── loop.py               # 主循环
├── cli.py                # 命令行入口
├── tui.py                # 终端界面
├── llm/
│   ├── base.py           # LLM 抽象基类
│   ├── mock.py           # 模拟 LLM（测试用）
│   └── openai.py         # 真实 LLM（OpenAI / DeepSeek）
└── tools/
    ├── file_tools.py     # 读文件、写文件
    └── shell.py          # 执行命令
```

### 1. models.py —— 一切从这里开始

这个文件定义了整个系统里所有"东西"长什么样。它不写任何逻辑，只定义数据类型。

**Message（消息）**：LLM 看到的是"一连串消息"，每条消息有角色和内容。

```python
@dataclass
class Message:
    role: str      # "system"（系统提示） / "user"（用户） / "assistant"（AI）
    content: str   # 消息内容
```

**Action（动作）**：LLM 决定"下一步做什么"之后，返回一个动作。

```python
@dataclass
class Action:
    tool: str             # 工具名，比如 "write_file"、"run_shell"
    params: dict           # 参数，比如 {"path": "bug.py", "content": "..."}
    thought: str = ""      # LLM 的思考过程
```

**ActionResult（动作结果）**：执行动作之后，得到的结果。

```python
@dataclass
class ActionResult:
    status: str            # "success" 或 "failure"
    message: str           # 结果描述
    metadata: dict = None  # 额外信息（比如 exit_code、stderr）
```

**Feedback（反馈）**：对 AI 产出的检查结果。

```python
@dataclass
class Feedback:
    status: str            # "pass" 或 "fail"
    summary: str           # 总结
    checks: list = None    # 每条检查的详细结果
    suggested_next_action: str = ""  # 建议 AI 下一步做什么
```

**为什么用 `@dataclass` 而不是字典？** 因为字典没有类型检查。你写 `msg["role"]` 拼错成 `msg["rol"]` 不会报错，但 `msg.role` 拼错了 IDE 会立刻提醒你。

### 2. config.py —— 把人的意图翻译成机器能读的

用户写一个 YAML 文件来控制 AI 的行为。`config.py` 负责读这个文件，转成 Python 对象。

```python
# config.yaml（用户写的）
llm:
  provider: deepseek
  model: deepseek-chat
  max_turns: 20
governance:
  blocked_commands:
    - "rm -rf"
    - "sudo"
```

```python
# config.py（代码读的）
@dataclass
class Config:
    llm_provider: str = "mock"          # 默认用 mock
    llm_model: str = "mock-model"
    llm_base_url: str = ""
    max_turns: int = 20
    blocked_commands: list = None
    auto_deny: bool = False

def load_config(path: str) -> Config:
    # 读 YAML 文件，转成 Config 对象
    # 没写的字段用默认值
```

**关键设计**：每个字段都有默认值，所以用户可以不写全部配置，系统也能正常工作。这就是"缺省配置"（sensible defaults）——让新手也能直接跑起来。

### 3. llm/ —— 抽象层：换模型不用改代码

这是整个项目最巧妙的设计之一。它定义了一个"接口"（抽象基类），然后让不同的 LLM 供应商去实现这个接口。

```python
# llm/base.py —— 抽象基类
class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[Message]) -> str:
        """给 LLM 发消息，返回回复文本"""
        pass
```

```python
# llm/mock.py —— 模拟 LLM，用于测试
class MockLLM(LLMProvider):
    def chat(self, messages):
        # 根据最后一句话返回预设的回复
        # 不调用任何网络，完全确定
        return '{"tool": "read_file", "params": {"path": "bug.py"}}'
```

```python
# llm/openai.py —— 真实 LLM
class OpenAILLM(LLMProvider):
    def chat(self, messages):
        # 调用 OpenAI 或 DeepSeek 的 API
        # 把 messages 转成 API 要求的格式
        # 返回 API 的回复文本
```

**为什么要这样设计？**

- 测试时用 MockLLM，不需要网络，不需要 API key，跑得飞快
- 换模型时，只要改配置文件里的 `provider` 字段，不用改代码
- 加新模型时，只要写一个新的类继承 `LLMProvider`，实现 `chat` 方法

这是面向对象编程里"多态"的典型应用。大一课程里学"继承"的时候，可能会觉得抽象——这里就是它最实在的用法。

### 4. parser.py —— 从人的语言里提取结构

LLM 返回的是自然语言文本，但系统需要的是结构化的 `Action` 对象。`parser.py` 负责这件事。

LLM 被要求返回 JSON 格式，比如：

```json
{
  "tool": "write_file",
  "params": {
    "path": "bug.py",
    "content": "def add(a, b):\n    return a + b"
  },
  "thought": "文件有语法错误，缺少冒号，我来修复"
}
```

`parser.py` 做的事情：

```python
def parse_action(text: str) -> Action:
    # 1. 从文本中提取最后一个 { ... } 块
    # 2. 用 json.loads 解析成字典
    # 3. 验证字段是否完整
    # 4. 返回 Action 对象
```

**为什么是"最后一个 JSON 块"？** 有些 LLM 会在 JSON 前后加解释文字，比如"好的，我来修复这个问题。\n\n```json\n{...}\n```\n\n这样就完成了。"。代码需要从这些文字里把 JSON 提取出来，而不是要求 LLM 只返回 JSON 不给任何文字。

### 5. governance.py —— 保安的逻辑

这个文件实现了"什么动作是危险的，需要拦截"。

```python
def check_action(action: Action, config: Config) -> tuple[bool, str]:
    """返回 (是否放行, 理由)"""
    
    # 检查 1：命令黑名单
    if action.tool == "run_shell":
        cmd = action.params.get("command", "")
        for blocked in config.blocked_commands:
            if blocked in cmd:
                return False, f"命令包含黑名单词: {blocked}"
    
    # 检查 2：文件路径限制（不能写到项目外面去）
    if action.tool == "write_file":
        path = Path(action.params["path"])
        if not path.resolve().is_relative_to(Path.cwd()):
            return False, "不能写到当前目录之外"
    
    return True, ""
```

**它不依赖 LLM**。这不是一句"请 AI 注意安全"的提示词，而是一个纯 Python 函数。你给它一个 `Action(command="rm -rf /")`，它永远返回"拦截"。这就是 §A.4 说的"机制必须是代码，不能是提示词"。

### 6. feedback.py —— 质检员的逻辑

LLM 执行完动作后，系统检查结果。这个检查分三个阶段：

```python
def collect(action_result, action, config) -> Feedback:
    checks = []
    
    # 阶段 1：基础检查——看 action_result 的状态
    checks.append(basic_check(action_result))
    
    # 阶段 2：语法检查——如果是写文件，用 py_compile 检查语法
    if action.tool == "write_file":
        checks.append(syntax_check(action_result))
    
    # 阶段 3：模式分析——看连续失败次数
    checks.append(pattern_analysis(history))
    
    # 汇总：有任何一个失败就返回 fail
    failed = [c for c in checks if c.status == "fail"]
    if failed:
        return Feedback(status="fail", checks=failed, 
                       suggested_next_action="先读取文件看看当前内容")
    return Feedback(status="pass")
```

**阶段 2 的语法检查是怎么做的？**

```python
def syntax_check(result: ActionResult) -> CheckResult:
    path = result.metadata.get("path", "")
    try:
        py_compile.compile(path, doraise=True)
        return CheckResult("syntax", "pass", "语法正确")
    except PyCompileError as e:
        return CheckResult("syntax", "fail", str(e))
```

这里用到了 Python 标准库的 `py_compile` 模块，它可以在不运行代码的情况下检查语法是否正确。这是一个**确定性校验器**——同一段代码，每次检查结果都一样。

### 7. memory.py —— 让 AI 有记忆

每次 LLM 调用时，需要把"历史对话"和"之前的反馈结果"一起发给它，否则它不知道之前发生了什么。

```python
class Memory:
    def __init__(self):
        self.messages = []      # 当前会话的消息列表
        self.history = []       # 跨会话的持久化记忆
    
    def append(self, role: str, content: str):
        """添加一条消息"""
        self.messages.append(Message(role=role, content=content))
    
    def append_hint(self, hint: str):
        """添加一条系统提示中的 hint（反馈闭环用）"""
        self.messages.append(Message(role="system", 
                             content=f"[Hint] {hint}"))
    
    def get_context(self) -> list[Message]:
        # 返回给 LLM 的全部消息
        # 包括系统提示 + 历史消息 + 当前会话消息
        return self.system_prompt + self.messages
```

**关键设计**：`append_hint` 方法专门用于反馈闭环。当反馈检测到问题（比如语法错误），系统会注入一条 `[Hint]` 消息，告诉 LLM"你刚才写的文件有语法错误，请修复"。这样 LLM 就知道了自己的错误，并据此修正。

### 8. loop.py —— 大脑：主循环

这是整个系统的核心，一个 while 循环，每次循环做 6 件事：

```python
def run(task: str, config: Config):
    memory = Memory()
    memory.append("user", task)     # 把用户任务放进去
    
    for turn in range(config.max_turns):
        # 步骤 1：组装上下文
        context = memory.get_context()
        
        # 步骤 2：调用 LLM
        llm = create_llm(config)     # 根据配置创建 LLM 实例
        response = llm.chat(context)  # 问 LLM 下一步做什么
        
        # 步骤 3：解析回复
        action = parse_action(response)  # 从文本中提取 Action
        
        # 步骤 4：安全检查
        allowed, reason = check_action(action, config)
        if not allowed:
            memory.append("system", f"动作被拦截: {reason}")
            continue
        
        # 步骤 5：执行动作
        if action.tool == "read_file":
            result = read_file(action.params["path"])
        elif action.tool == "write_file":
            result = write_file(action.params["path"], action.params["content"])
        elif action.tool == "run_shell":
            result = run_shell(action.params["command"])
        
        # 步骤 6：收集反馈
        feedback = feedback_collector.collect(result, action, config)
        
        # 把结果放回记忆，让 LLM 看到
        memory.append("tool", result.message)
        if feedback.status == "fail":
            # 注入 hint，让 LLM 知道哪里错了
            memory.append_hint(feedback.summary)
            for check in feedback.checks:
                memory.append_hint(check.detail)
        
        # 步骤 7：判断是否结束
        if feedback.status == "pass" and "task_complete" in action.tool:
            break
```

**这就是一个 agent 主循环的全部秘密**。没有魔法，就是一个 while 循环，每次问 LLM"下一步做什么"，然后执行，检查结果，把结果告诉 LLM，再问它"下一步做什么"。

### 9. tools/ —— 让 AI 能真正干活

工具是 LLM 和外部世界的桥梁。LLM 只是"想"，工具让它可以"做"。

**read_file**：读文件内容返回给 LLM。

```python
def read_file(path: str) -> ActionResult:
    try:
        content = Path(path).read_text(encoding="utf-8")
        # 限制长度，防止 LLM 上下文爆炸
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"
        return ActionResult("success", content)
    except Exception as e:
        return ActionResult("failure", str(e))
```

**write_file**：写文件。

```python
def write_file(path: str, content: str) -> ActionResult:
    # 安全检查：只能写在当前目录下
    abs_path = Path(path).resolve()
    if not abs_path.is_relative_to(Path.cwd()):
        return ActionResult("failure", "路径超出范围")
    
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding="utf-8")
    return ActionResult("success", f"已写入 {len(content)} 字符")
```

**run_shell**：执行命令（有超时限制）。

```python
def run_shell(command: str, timeout: int = 30) -> ActionResult:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return ActionResult(
            "success" if result.returncode == 0 else "failure",
            result.stdout or result.stderr,
            metadata={"exit_code": result.returncode}
        )
    except subprocess.TimeoutExpired:
        return ActionResult("failure", "命令执行超时")
```

### 10. tui.py —— 让命令行变得好看

TUI（Terminal UI）使用 `rich` 库，把枯燥的文本输出变成漂亮的界面。

```python
# 在终端里显示 4 个面板
layout = Layout()
layout.split_column(
    Layout(name="task", size=3),      # 显示当前任务
    Layout(name="thinking", size=8),  # 显示 LLM 的思考过程
    Layout(name="action"),            # 显示当前动作
    Layout(name="result"),            # 显示执行结果
)
```

每次主循环更新时，TUI 刷新对应面板的内容。用户看到的是实时更新的界面，而不是一行行滚动的文本。

### 11. cli.py —— 入口

用户输入 `harness run "..."` 时，`cli.py` 负责解析命令，加载配置，调用主循环。

```python
# 使用 click 或 argparse 解析命令行参数
@click.command()
@click.argument("task")
@click.option("--config", default="config.yaml")
def run(task, config):
    cfg = load_config(config)
    run_loop(task, cfg)
```

### 整体数据流（用图画出来）

```
用户输入任务
    │
    ▼
Memory (存储消息)
    │
    ▼
LLM (决定下一步做什么)
    │
    ▼
Parser (解析回复为 Action)
    │
    ▼
Governance (安全检查)
    │
    ├── 拦截 → 告诉 LLM "被拦截了" → 回到 LLM
    │
    ▼
Tools (执行动作: 读/写文件、跑命令)
    │
    ▼
Feedback (检查结果)
    │
    ├── 失败 → 注入 Hint → 回到 LLM
    │
    ▼
判断是否完成
    ├── 完成 → 结束
    └── 未完成 → 回到 LLM
```

### 这个架构为什么好？

1. **每个环节可以独立测试**。你想测试 governance，不用启动 LLM，不用读写文件，直接传一个 Action 进去，断言返回值。
2. **每个环节可以独立替换**。想换 LLM 供应商？改一行配置。想加新工具？在 `tools/` 里加一个函数，注册就行。
3. **数据流是单向的**。LLM → 解析 → 治理 → 执行 → 反馈 → 回到 LLM，没有循环依赖，没有"谁调谁"的混乱。

### 大一学生能从这个架构里学到什么

- **不要把代码都写在一个文件里**。每个文件只做一件事，改了不会影响其他文件。
- **用抽象基类定义接口**。`LLMProvider` 让"换模型"变成改一行配置，而不是改 100 行代码。
- **数据流要单向**。A 调 B，B 调 C，不要 A 调 B 又调回 A。
- **每个模块要有自己的测试**。88 个测试覆盖了每个模块，任何改动都能立刻知道有没有破坏原来的功能。
- **配置和代码分离**。用户改 YAML 就行，不用碰代码。
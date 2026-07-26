# REFLECTION.md — 反思报告

> 本反思报告由学生本人撰写，AI 辅助润色。

## 一、哪些技能发挥最大作用、哪些形式大于实质

**brainstorming** 发挥最大作用。它通过"分块呈现、逐节确认"强制我在写代码前把设计想清楚，产出了 SPEC.md 12 节内容，每节经用户确认才进入下一节，避免了"一次性输出后才发现方向错误"的浪费。

**subagent-driven-development** 第二有用。16 个 Phase 1 Task 和 8 个 Phase 2 Task 逐个派发给全新 subagent，每个只看到自己的 task 上下文。好处：subagent 不被无关信息干扰，我的主上下文也不被实现细节污染。Phase 1 的 13 个 subagent 全部一次通过，Phase 2 的 8 个中 7 个一次通过。

**TDD** 是放大器而非阻碍。88 个测试全程"先红→绿→commit"，给了 subagent 明确的"完成"信号，避免了"差不多就交"的模糊地带。

**using-git-worktrees** 形式大于实质。个人项目 16 个 task 串行执行，worktree 隔离优势不明显，用 dev 分支替代即可。**finishing-a-development-branch** 的四选项在个人项目中也略冗余，但其"验证测试→再合并"纪律有价值。

## 二、subagent 能自主运行多久、最优 task 颗粒度

Phase 1 的 13 个 subagent 全部一次通过无需干预。Phase 2 的 8 个中 7 个一次通过，Task 7 因 Windows 路径 JSON 转义中断后重新派发完成。subagent 未偏离主题，归功于 PLAN 中每个 task 都有完整代码——subagent 本质上在做"转录+测试"而非"设计+实现"。

**最优颗粒度**：一个 task 应是一个 subagent 在一次会话内能完成、有独立测试周期的单元。本次 24 个 task 颗粒度在"1-2 文件 + 3-7 测试"级别，足够小到不跑偏，又足够大到有评审价值。

## 三、SPEC/PLAN 质量如何影响实现质量

冷启动验证是最直接证据：陌生 subagent 仅凭 SPEC+PLAN 实现了 Task 1/2/5，12 个测试全部通过，无 spec 缺陷。但 PLAN 中的代码在 Windows 上有 3 个兼容性问题（单引号、断言文本、logging 顺序），因为 brainstorming 和 writing-plans 都在"理想环境"中编写，未实际运行。

**规约不清导致偏离的案例**：系统提示词没告诉 LLM 当前运行平台，DeepSeek 默认用 Linux 命令在 Windows 上全部失败，agent 在 20 轮中绕圈。修复方法是加入 `platform.system()`。这本质上是 SPEC 未明确"系统提示词应包含运行环境信息"。

## 四、最有效的 prompt/context 策略

**只给 subagent 它那一个 task 的内容**，不提供其他 task 上下文，避免 context 污染。具体做法：告诉 subagent "读 PLAN.md 的 Task N 部分"。

**系统提示词动态生成**：从静态字符串改为 `platform.system()` 动态生成后，LLM 立刻知道在 Windows 上，不再用 Linux 命令。这证明"上下文比提示词更重要"——与其写"请注意平台差异"，不如直接告诉它"你在 Windows 上"。

## 五、凭据与分发迫使我想清楚的问题

**凭据安全**逼我考虑完整威胁模型：key 不能进 Git 历史、日志、终端 history、明文配置。最终选 keyring 为主方案，环境变量为 Docker 回退，SPEC 列出 6 种威胁和对策。

**分发**逼我做"全新机器从零运行"检验：Docker COPY 顺序、key 如何传入容器、build-backend 是否有效（PLAN 中的值是错的，subagent 发现并修复）。

## 六、如果重做会改变什么

1. **PLAN 代码应在 Windows 上跑一遍**：3 个兼容性问题 + Phase 2 的 JSON 路径转义都是"写了没跑"导致的。
2. **系统提示词应在 SPEC 阶段设计好**：平台信息、JSON 格式、工具列表是 agent 行为的关键决定因素。
3. **应更早接入真实 LLM**：mock 只验证机制，"LLM 是否遵循 JSON 格式"只有真实 LLM 能回答。
4. **Phase 2 设计需更严谨**：初版有 4 个问题（"自修正"概念混淆、模式分析读错字段、与 SPEC 不对齐、未提及更新 SPEC），到实现时才暴露。
5. **最终评审能发现 task 级评审遗漏的集成问题**：hint 顺序颠倒和模式分析未检查连续性，都是跨 task 问题。

## 七、对 Superpowers 方法论的批判

1. **假设"规约足够清晰就能实现正确"**——大部分成立，但平台兼容性等"环境知识"无法靠规约传递。冷启动验证只验证"subagent 能否理解 spec"，未验证"spec 是否覆盖所有运行时需求"。

2. **假设"TDD 能保证实现质量"**——TDD 保证机制正确性，但不保证"真实 LLM 遵循格式约定"。88 个测试全通过，但接入 DeepSeek 后立刻遇到 tool_call_id 格式和平台感知问题。

3. **假设"subagent 能自主完成 task"**——当 PLAN 有完整代码时成立，但 subagent-driven 的成功高度依赖 PLAN 质量，而 PLAN 质量又依赖 brainstorming 深度，链条任何一环薄弱都会传导下游。

4. **假设"git worktree 隔离必要"**——个人小项目中 worktree 价值不如分支，且 subagent-driven 要求串行执行，worktree 隔离优势无法发挥。

总体而言，Superpowers 守住了 TDD、评审、计划这些 AI 协作中容易松懈的纪律，是有价值的"流程脚手架"。但七步工作流对个人项目偏重，可根据规模裁剪——用分支替代 worktree、用快速冷启动替代完整评审。

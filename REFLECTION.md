# REFLECTION.md — 反思报告

> 本反思报告由学生本人撰写，AI 辅助润色。

## 一、哪些 Superpowers 技能发挥了最大作用

**brainstorming** 是发挥最大作用的技能。它通过"分块呈现设计、逐节确认"的方式，强制我在写任何代码之前把设计想清楚。在本次项目中，brainstorming 产出了 SPEC.md 的 12 节内容，每一节都经过用户确认才进入下一节。这种增量验证避免了"一次性输出大量内容后才发现方向错误"的浪费。

**subagent-driven-development** 是第二有用的技能。它将 16 个 Phase 1 Task 和 8 个 Phase 2 Task 逐个派发给全新 subagent 实现，每个 subagent 只看到自己那一个 task 的上下文。这带来了两个好处：一是 subagent 不会被无关信息干扰，专注度高；二是我的主上下文不会被实现细节污染，可以专注于协调和评审。实际执行中，Phase 1 的 13 个 subagent 全部一次通过，Phase 2 的 8 个 subagent 中 7 个一次通过，1 个因 Windows 路径 JSON 转义问题需要 fix subagent 修复。

**test-driven-development** 作为硬性要求贯穿全程。每个 task 都是"先写失败测试→验证红色→写最小实现→验证绿色→commit"。88 个测试在最终评审时全部通过，且冷启动验证证明这些测试在陌生 agent 手中也能直接运行。TDD 在 AI 协作下不是阻碍，而是放大器——它给了 subagent 明确的"完成"信号，避免了"实现差不多就交"的模糊地带。

## 二、哪些技能"形式大于实质"

**using-git-worktrees** 在本次项目中形式大于实质。作业要求"每个独立功能开一个 worktree 对应一个 PR"，但实际操作中我用了 dev 分支替代 worktree。原因是个人项目规模不大，16 个 task 串行执行，worktree 的隔离优势不明显，反而增加了目录切换的复杂度。如果项目更大、有并行 task，worktree 的价值才会体现。

**finishing-a-development-branch** 的四个选项（合并/PR/保留/丢弃）在个人项目中略显冗余。个人项目直接合并到 master 即可，不需要 PR 评审流程。但这个技能的"验证测试→再合并"纪律是有价值的。

## 三、subagent-driven 工作流让智能体能自主运行多久

在本次项目中，Phase 1 的 13 个实现 subagent 全部一次通过，无需人工干预。Phase 2 的 8 个 subagent 中 7 个一次通过，Task 7 因 Windows 路径在 JSON 中需转义而中断，重新派发后完成。最长的一个 subagent（Task 12 CLI+Keyring）处理了 4 个测试文件和 140 行实现代码，耗时约 3 分钟。subagent 没有偏离主题的情况发生，这归功于 PLAN.md 中每个 task 都有完整的代码——subagent 本质上是在做"转录+测试"，而非"设计+实现"。

但如果 PLAN 中只有描述没有代码，subagent 的表现会显著下降。冷启动验证中，subagent 在没有 Task 1 依赖的情况下主动暂停提问，说明它不会凭猜测继续——这是好的。但如果给它一个只有描述没有代码的 task，它可能会做出与原意不一致的解读。

**最优 task 颗粒度**：一个 task 应该是一个 subagent 在一次会话内能完成的、有独立测试周期的单元。本次 Phase 1 的 16 个 task 和 Phase 2 的 8 个 task 颗粒度大致在"1-2 个文件 + 3-7 个测试"级别，实践证明这个大小是合适的——足够小到 subagent 不会跑偏，又足够大到有独立的评审价值。

## 四、SPEC/PLAN 质量如何影响实现质量

冷启动验证是 SPEC/PLAN 质量最直接的证据。陌生 subagent 仅凭 SPEC.md + PLAN.md 实现了 Task 1/2/5，12 个测试全部通过，无 spec 缺陷暴露。这说明当 SPEC 和 PLAN 足够清晰时，实现质量是可以预期的。

但 PLAN 中的代码在 Windows 上有 3 个兼容性问题（单引号不生效、断言文本不匹配、logging 顺序），这些是 SPEC/PLAN 阶段没有考虑到的。原因是 brainstorming 和 writing-plans 都在"理想环境"中编写代码，没有实际运行验证。这提示我：PLAN 中的代码应该是"参考实现"而非"最终实现"，subagent 需要有空间做平台适配。

**一个"规约不清导致 subagent 偏离"的具体案例**：系统提示词没有告诉 LLM 当前运行平台。在真实 LLM 验证中，DeepSeek 默认使用 Linux 命令（`cat << EOF`、`/tmp/`、`/home/user/`），在 Windows 上全部失败。agent 在 20 轮循环中一直绕圈，无法理解"为什么 Linux 命令不工作"。修复方法是在系统提示词中加入 `platform.system()` 和 `os.getcwd()`。这个问题本质上是 SPEC 中没有明确"系统提示词应包含运行环境信息"这一要求，导致实现时遗漏。

## 五、最有效的 prompt/context 策略

最有效的策略是**在 subagent 的 dispatch prompt 中只提供它那一个 task 的内容，不提供其他 task 的上下文**。这避免了 context 污染，subagent 专注于自己的任务。具体做法是：告诉 subagent "读 PLAN.md 中的 Task N 部分"，而不是把整个 PLAN 贴给它。

第二个有效策略是**系统提示词动态生成**。最初系统提示词是静态字符串，不包含平台信息。改为 `platform.system()` 动态生成后，LLM 立刻知道自己在 Windows 上，不再用 Linux 命令。这证明了"上下文比提示词更重要"——与其写"请注意平台差异"，不如直接告诉它"你在 Windows 上"。

## 六、凭据与分发迫使我想清楚的问题

**凭据安全**迫使我想清楚了"key 在哪里存储、如何流转、谁能看到"。最初我认为"不硬编码就行"，但作业要求逼我考虑了完整的威胁模型：key 不能进 Git 历史、不能进日志、不能进终端 history、不能进明文配置文件。最终选择了 keyring 作为主方案，环境变量作为 Docker 回退方案，并在 SPEC 中列出了 6 种威胁和对策。

**分发**迫使我想清楚了"别人如何在一台全新机器上从零运行"。Docker 方案需要考虑 COPY 顺序（源码必须在 pip install 之前）、key 如何传入容器（环境变量回退）、WORKDIR 与挂载卷的关系。PyPI 方案需要考虑 build-backend 是否有效（PLAN 中的值是错的，subagent 发现并修复了）。这些问题在"只在自己机器上跑"时不会暴露，但分发要求逼我做了一台新机器视角的检验。

## 七、如果重做我会改变什么

1. **PLAN 中的代码应该在 Windows 上实际跑一遍**：3 个 Windows 兼容性问题都是"写了没跑"导致的。如果 writing-plans 阶段就跑一遍测试，这些问题会在 PLAN 自审时被发现。
2. **系统提示词应该在 SPEC 阶段就设计好**：包括平台信息、JSON 格式要求、工具列表。这是 agent 行为质量的关键决定因素，不应该在实现后才发现缺失。
3. **冷启动验证应该选有依赖的 task**：我选了 Task 2 和 Task 5，它们都依赖 Task 1 但 Task 1 没做。虽然 subagent 正确识别了依赖，但这浪费了一轮交互。应该选 Task 1+2 或 Task 2+3（有依赖关系的连续 task）。
4. **应该更早接入真实 LLM 验证**：mock 测试只能验证机制正确性，但"LLM 是否遵循 JSON 格式"、"系统提示词是否足够"这些问题只有真实 LLM 才能回答。在 Task 11（loop）完成后就应该接入真实 LLM 试跑。
5. **Phase 2 设计文档需要更严谨**：初版设计文档有 4 个问题——"自修正"概念混淆（harness 不能自己修文件，只能注入 hint）、模式分析读错字段（从 feedback.metadata 取而非 action.tool）、与 SPEC 不对齐（承诺了 typecheck/coverage 但未实现）、未提及更新 SPEC。这些问题在设计阶段没有发现，到实现时才暴露。
6. **Windows 路径在 JSON 中需转义**：Phase 2 的测试在 Windows 上失败，因为 `tmp_path` 返回的路径含反斜杠，直接插入 JSON 会导致 `\U`、`\b` 等无效转义。修复方法是 `json.dumps(str(path))`。这再次证明了"PLAN 中的代码应该在 Windows 上实际跑一遍"。
7. **最终评审能发现 task 级评审遗漏的问题**：Phase 2 最终评审发现了 2 个 Important——hint 顺序颠倒（在 action/result 之前注入）和模式分析未检查连续性（只计数总数）。这两个问题在逐 task 评审中未被发现，因为它们是跨 task 的集成问题。

## 八、对 Superpowers 方法论的批判

Superpowers 假设了几个前提：

1. **假设"规约足够清晰就能实现正确"**——这在大部分情况下成立，但平台兼容性、API 格式差异等"环境知识"无法完全靠规约传递。冷启动验证虽然能发现 spec 缺陷，但它只验证了"subagent 能否理解 spec"，没有验证"spec 是否覆盖了所有运行时需求"。

2. **假设"TDD 能保证实现质量"**——TDD 能保证机制正确性（mock 测试通过），但不能保证"真实 LLM 会遵循你的格式约定"。我的 88 个测试全部通过，但接入 DeepSeek 后立刻遇到了两个问题（tool_call_id 格式、平台感知），这些是 mock 测试无法覆盖的。

3. **假设"subagent 能自主完成 task"**——当 PLAN 中有完整代码时成立（13/13 一次通过），但当只有描述没有代码时可能不成立。subagent-driven 的成功高度依赖 PLAN 的质量，而 PLAN 的质量又依赖 brainstorming 的深度。这是一个链条，任何一环薄弱都会传导到下游。

4. **假设"git worktree 隔离是必要的"**——在个人小项目中，worktree 的隔离价值不如直接用分支。worktree 的真正价值在于多人协作或并行 task，但 subagent-driven 要求串行执行（"Never dispatch multiple implementation subagents in parallel"），所以 worktree 的隔离优势在单 subagent 串行模式下无法发挥。

总体而言，Superpowers 提供了一套有价值的"流程脚手架"，它守住了 TDD、评审、计划这些在 AI 协作中容易松懈的纪律。但它的七步工作流对于个人项目来说有些重，可以根据项目规模适当裁剪——例如用分支替代 worktree、用快速冷启动替代完整评审流程。

# Palimpsest / 忘筌

> 得鱼而忘筌；得意而忘言。

Palimpsest / 忘筌 是一个 local-first 的个人阅读知识基础设施。它的目标不是简单记录“我读过哪些书”，而是让阅读痕迹在未来的问题、项目和判断中重新显现。

```text
                 ·
          ·              ·

              ><(((º>

       water without water
       trace without capture
```

## 项目目标

这个项目想解决的是：如何最大化阅读的长期效用。

第一阶段先从豆瓣读书记录开始，把想读、在读、读过、评分、标签、短评等信息迁移进自己的数据库，并且每次导入都能验证：

- 原始输入有多少条。
- 成功解析了多少条。
- 成功写入数据库多少条。
- 哪些记录重复。
- 哪些字段缺失。
- 哪些匹配结果需要人工确认。

第二阶段会把书籍元数据、用户笔记、阅读状态和图谱关系呈现在网页中。图谱的价值不是“好看”，而是能解释书与书之间为什么相关。

长期目标是 `Ask My Library`：基于自己的书、笔记、划线、图谱和项目语境，回答“我读过什么可以帮助当前这个问题”。

## 名字

`Palimpsest` 指被反复书写、覆盖、擦除后仍保留旧痕迹的手稿。它对应这个项目的数据层：阅读痕迹会层层累积，并在新的问题中重新浮现。

`忘筌` 来自“得鱼而忘筌；得意而忘言”。它对应这个项目的产品哲学：书目、笔记、图谱、数据库和 AI 都只是工具，真正重要的是阅读之后形成的理解、判断和行动。

## 技术栈

MVP 技术栈：

- 前端：React + TypeScript + Vite。
- 后端：FastAPI。
- 数据库：SQLite 优先，保留迁移到 Postgres 的路径。
- 图谱渲染：D3，封装在 React component 内。
- 书籍元数据：Open Library / Google Books，后端 provider adapter 封装。
- Agent 协作：Codex GPT-5.5 负责规划、架构、验收；opencode + MiMo 负责实现任务包。

## 架构原则

项目强调低耦合：

```text
web -> api -> services -> repositories -> database
                 |
                 -> importers
                 -> metadata providers
                 -> graph builders
                 -> agent tools
```

明确禁止：

- parser 直接写数据库。
- LLM 直接写持久化记录。
- metadata provider 直接决定最终书籍记录。
- React 直接调用外部书籍 API。
- graph renderer 依赖豆瓣原始文本。

## 当前状态

当前处于早期 scaffold 和规划阶段：

- 已有 FastAPI health endpoint。
- 已有 React/Vite 前端壳。
- 已有项目 spec、实施计划、agent 协作协议和 git 管理约定。
- 已有 Claude Design 初步 UI 探索截图。

下一步重点是建立豆瓣粘贴导入的 fixtures，并以 TDD 方式实现解析和验证流程。

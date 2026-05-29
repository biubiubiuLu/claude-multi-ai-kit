# claude-multi-ai-kit

> 一套可一键部署的多 AI 协作脚手架：**GPT(Codex) 写计划 / DeepSeek(opencode) 写代码 / GPT(Codex) 审查与测试 / Gemini(Antigravity) 优化前端**。
> 默认走 CLI 模式复用本机已登录账号。

---

## 快速开始

当前最小可用入口：

```bash
/Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/cship \
  --repo /Users/lukai/IdeaProjects/weibo-talent-introduction \
  --plan-only \
  "按 historical-mail-automation-plan.md 开发 Sprint 4"
```

安全验证入口，不调用外部模型：

```bash
/Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/cship \
  --repo /path/to/project \
  --dry-run \
  --plan-only \
  "验证项目配置"
```

也可以安装到本机默认位置：

```bash
/Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/install.sh
/Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/doctor.sh
```

```bash
curl -fsSL https://raw.githubusercontent.com/<you>/claude-multi-ai-kit/main/install.sh | bash
```

详见 [`docs/03-install-guide.md`](docs/03-install-guide.md)。

## 文档地图

| 文件 | 受众 | 内容 |
|------|------|------|
| [`docs/01-architecture.md`](docs/01-architecture.md) | 设计 | 整体架构、角色分工、工具中立设计 |
| [`docs/02-implementation-spec.md`](docs/02-implementation-spec.md) | **实施者（DeepSeek）** | 仓库结构、CLI 包装器规范、install/upgrade/uninstall 行为、Planner 输出契约 |
| [`docs/03-install-guide.md`](docs/03-install-guide.md) | 最终用户 | 一键部署、日常使用、常见问题 |

## 角色与默认配置

| 角色 | Provider | 默认模式 | CLI / Key |
|------|----------|---------|-----------|
| Planner（开发计划） | GPT | `cli` | `codex` |
| Coder（写代码） | opencode + DeepSeek | `cli` | `opencode` |
| Reviewer（测试+审查） | GPT | `cli` | `codex` |
| Frontend（前端优化，**可关**） | Gemini | `cli` | `agy`（Google Antigravity） |

关闭前端优化：`FRONTEND_ENABLED=false` → 前端代码由 DeepSeek 按 Planner 计划直接写。

## 仓库结构

```
.
├── README.md
├── VERSION
├── install.sh / upgrade.sh / uninstall.sh / doctor.sh   # 待实现
├── docs/                                                 # 设计与使用文档
├── scripts/                                              # 4 个对等 CLI + ship.py（待实现）
├── agents/                                               # Claude Code 子 Agent 定义
├── commands/                                             # /ship slash command
├── templates/                                            # .env / settings.json / CLAUDE.md 模板
└── tests/                                                # smoke_test + 单测
```

## 当前状态

🟡 **P1/P2/P3 最小可用版已实现，升级/卸载待实现**。当前已有 CLI wrapper、`ship.py` 编排器、最小安装器和 doctor；升级、卸载和完整 smoke test 继续按 [`docs/02-implementation-spec.md`](docs/02-implementation-spec.md) 分阶段实现：

- P1 · `ai_common.py` + 4 个 CLI 包装器（已实现）
- P2 · `ship.py` 编排器（已实现）
- P3 · `install.sh` / `doctor.sh` / 模板（最小版已实现）
- P4 · `upgrade.sh` / `doctor.sh` / `kit.lock`
- P5 · Claude Code 适配层（agents + ship.md）
- P6 · README 完善 + smoke test

## License

私有仓库，仅自用。

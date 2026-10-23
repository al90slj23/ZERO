# L0/workflows - CI/CD 工作流

**定位**：管理项目的 CI/CD 工作流配置，按平台分类存储。

---

## 目录结构

```
.ai/L0#Execution/workflows/
├── README.md          # 本文档
├── github/            # GitHub Actions 工作流
│   └── *.yml
├── gitlab/            # GitLab CI 工作流
│   └── *.yml
└── local/             # 本地开发工作流
    └── *.sh
```

---

## 平台分类

### github/ - GitHub Actions
- **文件格式**：`.yml` / `.yaml`
- **部署位置**：`.github/workflows/`
- **触发方式**：push、pull_request、schedule 等

### gitlab/ - GitLab CI
- **文件格式**：`.gitlab-ci.yml`
- **部署位置**：项目根目录
- **触发方式**：push、merge_request、schedule 等

### local/ - 本地工作流
- **文件格式**：`.sh` / `.js` / `.ts`
- **执行方式**：手动执行或通过 hooks 触发
- **用途**：本地开发、测试、部署脚本

---

## 工作流命名规范

### GitHub Actions
```
{功能}-{触发条件}.yml

示例：
- ci-test-on-push.yml          # 推送时运行测试
- deploy-production-on-tag.yml # 标签时部署生产
- lint-on-pr.yml               # PR 时运行 lint
```

### 本地脚本
```
{功能}-{环境}.sh

示例：
- deploy-staging.sh            # 部署到测试环境
- backup-database.sh           # 备份数据库
- sync-assets.sh               # 同步静态资源
```

---

## 创建新工作流

### GitHub Actions
```bash
# 1. 创建工作流文件
touch .ai/L0#Execution/workflows/github/my-workflow.yml

# 2. 编写配置
vim .ai/L0#Execution/workflows/github/my-workflow.yml

# 3. 复制到 GitHub Actions 目录
cp .ai/L0#Execution/workflows/github/my-workflow.yml .github/workflows/
```

### 本地脚本
```bash
# 1. 创建脚本
touch .ai/L0#Execution/workflows/local/my-script.sh

# 2. 编写脚本
vim .ai/L0#Execution/workflows/local/my-script.sh

# 3. 设置可执行权限
chmod +x .ai/L0#Execution/workflows/local/my-script.sh

# 4. 执行
.ai/L0#Execution/workflows/local/my-script.sh
```

---

## 工作流模板

### GitHub Actions 基础模板
```yaml
name: CI Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
```

### 本地部署脚本模板
```bash
#!/bin/bash
set -e

echo "开始部署..."

# 1. 拉取最新代码
git pull origin main

# 2. 安装依赖
npm install

# 3. 构建
npm run build

# 4. 重启服务
pm2 restart app

echo "部署完成！"
```

---

## 注意事项

1. **敏感信息**：不要在工作流中硬编码密钥，使用环境变量
2. **版本控制**：工作流文件应纳入 Git 版本控制
3. **测试验证**：新工作流先在测试环境验证
4. **文档完整**：在工作流中添加注释说明用途

---

## 常见工作流

### 知识检索自动适配

新项目与既有项目先使用 `local/zero-bootstrap.sh --target <项目> --prepare-only`，由 Agent 完成首次适配后执行完整模式。它保留并备份目标资料、合并 `.ai` 模板与 Codex 连接，然后调用检索 `init`。参见 [首次引入指南](../../L3%23Standards/references/zero-first-use.md)。

`local/retrieval-indexes.sh` 是 QMD / CodeGraph 的启动和收尾入口：首次自动构建配置和索引，之后自动补齐变化。客户端用 `qmd-mcp`、`codegraph-mcp` 启动，Agent 在知识源变更后执行 `refresh`，`status` 用于检查。所有真实数据放在 `.ai/L5#Knowledge/.generated/`；根 `.codegraph` 仅为自动生成的软链。

此脚本从采用项目的根目录运行，依赖 Bash、Python 3（macOS/Linux 文件锁）、Node.js 22+ 与 npm，自动按 L0 toolchain 锁定版本安装本地 CLI。`setup` 仅安装工具，`init` 预拉模型并完成初次索引。QMD MCP 启动后台补齐，普通读取使用现有索引，收尾 `refresh` 等待互斥刷新完成。接入详见 [检索适配规范](../../L3%23Standards/standards/10.ai-memory-04.retrieval-adapters.md)。

| 工作流 | 触发条件 | 用途 |
|--------|---------|------|
| CI 测试 | push / PR | 运行单元测试、集成测试 |
| 代码检查 | push / PR | 运行 lint、type-check |
| 自动部署 | push to main | 部署到生产环境 |
| 定时任务 | schedule | 数据备份、清理缓存 |

---

**最后更新**：2026-04-16

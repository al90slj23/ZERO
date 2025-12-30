# ZERO 框架迭代流程

> **文档版本**：v1.0.0
> **创建日期**：2025-12-30
> **文档位置**：`{项目根目录}/ZERO/docs/ZERO-ITERATION.md`

---

## 📍 文档定位

本文档定义 **ZERO 框架本身**的迭代开发流程。

**这是 ZERO 框架的元文档**，不属于 `standards/` 规范体系。

**重要区分**：
- **本文档**：ZERO 框架的迭代（模板本身的更新）
- **standards/**：应用 ZERO 模板的项目应遵循的规范

**ZERO 位置约定**：
- ZERO 框架始终位于使用它的项目根目录下的 `/ZERO/` 目录
- 例如：`/path/to/your-project/ZERO/`

---

## 🎯 核心问题

### 为什么需要规范迭代流程

ZERO 框架可能被多个项目引用，在不同项目中开发时可能会优化 ZERO，导致：

1. **版本混乱**：不同项目中的 ZERO 副本版本不一致
2. **合并困难**：各项目独立修改，难以合并回主仓库
3. **丢失改进**：某个项目中的优化没有同步到其他项目

### 解决方案

**单一源头原则**：所有 ZERO 的修改都必须通过主仓库进行。

```
GitHub 主仓库 (al90slj23/ZERO)
        ↓ 拉取最新
    本地开发
        ↓ 修改完成
    推送回主仓库
        ↓ 其他项目
    从主仓库更新
```

---

## 📋 迭代流程

### 第一步：拉取最新版本

**每次修改 ZERO 前，必须先从 GitHub 拉取最新版本。**

```bash
# 进入项目根目录下的 ZERO 目录
cd /path/to/your-project/ZERO

# 检查当前状态
git status

# 如果有本地修改，先暂存或放弃
git stash  # 暂存本地修改
# 或
git checkout .  # 放弃本地修改

# 拉取最新版本
git pull origin main
```

### 第二步：进行修改

在本地进行 ZERO 框架的修改：

```bash
# 修改文件
vim docs/standards/xxx.md
vim go.lib.sh
# ...

# 测试修改
./go.sh
```

### 第三步：提交并推送

```bash
# 查看修改
git status
git diff

# 提交修改
git add .
git commit -m "feat: 添加 .deployignore 规范"

# 推送到 GitHub
git push origin main
```

### 第四步：更新其他项目

其他使用 ZERO 的项目需要更新：

```bash
# 进入其他项目根目录下的 ZERO 目录
cd /path/to/other-project/ZERO

# 拉取最新版本
git pull origin main
```

---

## 🔄 快速命令

### 一键更新 ZERO

在项目根目录执行：

```bash
# 进入 ZERO 目录并更新
cd ZERO && git pull origin main && cd ..
```

或创建脚本 `update-zero.sh`（放在项目根目录）：

```bash
#!/bin/bash
# 更新项目根目录下的 ZERO 框架到最新版本

ZERO_DIR="ZERO"

if [ ! -d "$ZERO_DIR" ]; then
    echo "❌ 未找到 ZERO 目录"
    exit 1
fi

cd "$ZERO_DIR"

# 检查是否有本地修改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  ZERO 有本地修改，请先处理："
    git status -s
    exit 1
fi

# 拉取最新版本
echo "📥 拉取 ZERO 最新版本..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ ZERO 已更新到最新版本"
else
    echo "❌ 更新失败"
    exit 1
fi
```

### 一键提交 ZERO 修改

```bash
#!/bin/bash
# 提交项目根目录下的 ZERO 修改到 GitHub

ZERO_DIR="ZERO"

cd "$ZERO_DIR"

# 检查是否有修改
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  没有需要提交的修改"
    exit 0
fi

# 显示修改
echo "📝 待提交的修改："
git status -s
echo ""

# 确认提交
read -p "确认提交？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

# 输入提交信息
read -p "请输入提交信息: " message
if [ -z "$message" ]; then
    message="chore: 更新 ZERO 框架"
fi

# 提交并推送
git add .
git commit -m "$message"
git push origin main

echo "✅ 已提交并推送到 GitHub"
```

---

## ⚠️ 注意事项

### 1. 不要在项目中直接修改 ZERO 而不提交

❌ **错误做法**：
```bash
# 在项目 A 的 ZERO 目录中直接修改，不提交到 GitHub
cd /project-a/ZERO
vim docs/standards/xxx.md
# 修改后不提交，继续开发项目 A
```

✅ **正确做法**：
```bash
# 1. 先拉取最新
cd /project-a/ZERO
git pull origin main

# 2. 修改
vim docs/standards/xxx.md

# 3. 提交到 GitHub
git add .
git commit -m "feat: xxx"
git push origin main

# 4. 其他项目更新
cd /project-b/ZERO
git pull origin main
```

### 2. ZERO 是独立 Git 仓库

ZERO 目录有自己的 `.git`，与父项目的 Git 是独立的。

```
your-project/           # 项目根目录
├── .git/               # 项目的 Git
├── ZERO/               # ZERO 框架目录
│   ├── .git/           # ZERO 的 Git（独立仓库）
│   └── ...
└── ...
```

### 3. ZERO 位置固定

ZERO 框架始终位于项目根目录下的 `/ZERO/` 目录，不要放在其他位置。

### 3. 版本标签

重要版本应该打标签：

```bash
cd ZERO
git tag -a v1.1.0 -m "添加 .deployignore 规范"
git push origin v1.1.0
```

---

## 📊 版本管理

### 版本号规则

遵循语义化版本：`MAJOR.MINOR.PATCH`

| 类型 | 说明 | 示例 |
|------|------|------|
| MAJOR | 不兼容的重大变更 | 1.0.0 → 2.0.0 |
| MINOR | 新增功能（向后兼容） | 1.0.0 → 1.1.0 |
| PATCH | Bug 修复 | 1.0.0 → 1.0.1 |

### 更新日志

在 `ZERO/CHANGELOG.md` 中记录变更：

```markdown
# Changelog

## [1.1.0] - 2025-12-30

### Added
- 新增 .deployignore 部署排除规则规范
- go.lib.sh 添加 build_rsync_excludes 函数

### Changed
- go.2.sh 使用配置文件而非硬编码排除规则
```

---

## ✅ 检查清单

修改 ZERO 前：
- [ ] 已拉取最新版本 (`git pull origin main`)
- [ ] 本地没有未提交的修改

修改 ZERO 后：
- [ ] 已测试修改是否正常工作
- [ ] 已提交到 GitHub (`git push origin main`)
- [ ] 已更新 CHANGELOG.md（如果是重要变更）
- [ ] 已通知其他项目更新（如果需要）

---

**最后更新**：2025-12-30

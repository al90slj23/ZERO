# ZERO 文档结构迁移指南

> **迁移日期**：2026-04-16
> **版本**：v2.0.0
> **变更**：`rules/` → `.ai/` 七层架构

---

## 📋 变更摘要

### 原始结构（v1.x）

```
ZERO/
├── rules/
│   ├── standards/
│   ├── condensed/
│   ├── references/
│   └── inspirations/
└── worklogs/
```

### 新结构（v2.0）

```
ZERO/
└── .ai/                                # 七层架构
    ├── L0/                             # 项目进度管理
    │   ├── specs/
    │   ├── hooks/
    │   ├── skills/
    │   └── workflows/
    ├── L1/                             # 启动引导（1个文件）
    │   └── README.md
    ├── L2/                             # 分类索引（11个文件）
    │   ├── 00.meta.md
    │   ├── 01.arch.md
    │   └── ...
    ├── L3/                             # 精炼规范（~60个文件）
    │   ├── 00.meta-01.core.md
    │   └── ...
    ├── L4/                             # 完整规范
    │   ├── standards/
    │   ├── references/
    │   ├── adr/
    │   └── philosophy/
    ├── L5/                             # 操作日志
    │   └── {YYYY}/{MM}/{YYYY-MM-DD}.{type}-{topic}.md
    └── L6/                             # 知识图谱（可选）
        └── README.md
```

---

## 🎯 迁移原因

### 问题
1. **目录冲突**：`rules/` 与使用 ZERO 的项目中的 `rules/` 可能产生冲突
2. **层级不清**：`standards/` 和 `condensed/` 的关系不够明确
3. **缺少层级**：没有 L0（进度管理）、L1（启动引导）、L2（分类索引）、L5（操作日志）、L6（知识图谱）
4. **工具专属**：`.ai-example/` 目录名不够通用

### 解决方案
1. **统一目录名**：`.ai/` 是 AI 记忆体系的标准目录名
2. **七层架构**：L0-L6 清晰的层级划分，每层职责明确
3. **蒸馏金字塔**：信息从下往上逐层蒸馏提纯
4. **工具无关**：`.ai/` 目录独立于任何 IDE/CLI 工具

---

## 📝 路径更新

### 文档链接

| 原始路径 | 新路径 |
|---------|--------|
| `ZERO/rules/standards/` | `ZERO/.ai/L4/standards/` |
| `ZERO/rules/condensed/` | `ZERO/.ai/L3/` |
| `ZERO/rules/references/` | `ZERO/.ai/L4/references/` |
| `ZERO/rules/inspirations/` | `ZERO/.ai/L4/inspirations/` |
| `ZERO/worklogs/` | `ZERO/.ai/L5/` |
| `ZERO/.ai-example/L0/` | `ZERO/.ai/L0/` |
| `ZERO/.ai-example/L6/` | `ZERO/.ai/L6/` |

### 链接修改示例

```markdown
# 旧链接
[规范](./rules/standards/00.meta-01.core.md)
[精炼版](./rules/condensed/00.meta-01.core.md)

# 新链接
[规范](./.ai/L4/standards/00.meta-01.core.md)
[精炼版](./.ai/L3/00.meta-01.core.md)
```

---

## 🔄 迁移步骤

### 对于现有 ZERO 用户

1. **更新 Git 仓库**
   ```bash
   cd ZERO
   git pull origin main
   ```

2. **更新项目配置**
   如果项目中有硬编码的 ZERO 文档路径，需要更新：
   ```bash
   # 查找所有 ZERO/rules 的引用
   grep -r "ZERO/rules" .
   
   # 替换为新路径
   sed -i 's|ZERO/rules/standards|ZERO/.ai/L4/standards|g' file.txt
   sed -i 's|ZERO/rules/condensed|ZERO/.ai/L3|g' file.txt
   ```

3. **更新文档链接**
   如果在项目文档中有 ZERO 的链接，更新为新路径

4. **测试**
   确认所有链接都能正常访问

---

## 📚 规范访问指南

### 通过 ZERO 框架访问规范

```bash
# 查看 ZERO 规范
cat ZERO/.ai/L4/standards/00.meta-01.core.md

# 查看精炼版
cat ZERO/.ai/L3/00.meta-01.core.md

# 查看参考实现
cat ZERO/.ai/L4/references/admin-layout.md

# 查看操作日志
ls ZERO/.ai/L5/2026/04/
```

### 在项目中引用 ZERO 规范

```markdown
# 在项目文档中引用 ZERO
[ZERO 元规范](../ZERO/.ai/L4/standards/00.meta-01.core.md)
[ZERO 快速参考](../ZERO/README.md)
[ZERO 架构说明](../ZERO/.ai/L4/standards/10.ai-memory-01.architecture.md)
```

---

## ⚠️ 注意事项

### 对 ZERO 开发者

1. **保持向后兼容**
   - 旧链接可以通过 Git 历史访问
   - 建议在 README 中说明迁移信息

2. **更新所有文档**
   - 检查所有 markdown 文件中的路径引用
   - 更新内部链接

3. **持续维护**
   - 新增文档时使用 `.ai/` 路径
   - 避免在 `rules/` 中添加新文件

### 对使用 ZERO 的项目

1. **更新 ZERO 后**
   - 确保项目文档正确引用 ZERO 规范
   - 测试所有链接

2. **文档引用**
   - 使用相对路径时注意目录结构
   - 考虑使用统一的规范引用模板

3. **IDE 映射**
   - 使用 `./gogogo.sh 8` 或 `./gogogo.sh ai` 管理 IDE 映射
   - 映射会自动从 `.ai/` 目录同步到各 IDE 的配置目录

---

## 🔗 相关文档

- `ZERO/README.md` - ZERO 框架说明
- `ZERO/.ai/L4/standards/10.ai-memory-01.architecture.md` - 七层架构详细说明
- `ZERO/.ai/L4/standards/10.ai-memory-02.naming.md` - 命名与格式规范

---

## ❓ FAQ

### Q: 为什么要改为 `.ai/` 七层架构？
A: 为了提供更清晰的层级划分，支持从 L0（进度管理）到 L6（知识图谱）的完整 AI 记忆体系，并且 `.ai/` 是独立于任何工具的标准目录名。

### Q: 旧链接还能用吗？
A: 旧链接可以通过 Git 历史访问，但建议更新为新路径以保持一致性。

### Q: 如何快速更新所有链接？
A: 使用 `sed` 或其他文本替换工具批量替换：
```bash
sed -i 's|ZERO/rules/standards|ZERO/.ai/L4/standards|g' *.md
sed -i 's|ZERO/rules/condensed|ZERO/.ai/L3|g' *.md
```

### Q: 这个变更对我的项目有影响吗？
A: 如果你的项目直接引用了 `ZERO/rules/` 的路径，需要更新为 `ZERO/.ai/` 路径。

### Q: 七层架构的每一层是什么？
A: 
- L0: 项目进度管理（specs/hooks/skills/workflows）
- L1: 启动引导（概览+零容忍规则，1个文件）
- L2: 分类索引（11个分类，≤50行/文件）
- L3: 精炼规范（~60个文件，100-150行/文件）
- L4: 完整规范（无限制）
- L5: 操作日志（append-only）
- L6: 知识图谱（可选，语义搜索）

---

**最后更新**：2026-04-16
**版本**：2.0.0

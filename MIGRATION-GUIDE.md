# ZERO 文档结构迁移指南

> **迁移日期**：2026-04-12
> **版本**：v1.1.0
> **变更**：`docs/` → `specification/`

---

## 📋 变更摘要

### 原始结构

```
ZERO/
├── docs/
│   ├── standards/
│   ├── condensed/
│   ├── references/
│   └── inspirations/
```

### 新结构

```
ZERO/
├── specification/
│   ├── standards/
│   ├── condensed/
│   ├── references/
│   └── inspirations/
```

---

## 🎯 迁移原因

### 问题
1. **目录冲突**：`ZERO/docs/` 与使用 ZERO 的项目（如 AiLinkDog）中的 `docs/` 会产生冲突
2. **语义不清**：`docs/` 太通用，容易与项目的文档目录混淆
3. **路径复杂**：在项目中引用 ZERO 规范时需要特殊处理路径

### 解决方案
1. **使用专有目录名**：`specification/` 明确表示这是规范集合
2. **避免冲突**：与项目的 `docs/` 目录完全分离
3. **清晰结构**：项目结构更清晰

---

## 📝 路径更新

### 文档链接

| 原始路径 | 新路径 |
|---------|--------|
| `ZERO/docs/standards/` | `ZERO/specification/standards/` |
| `ZERO/docs/condensed/` | `ZERO/specification/condensed/` |
| `ZERO/docs/references/` | `ZERO/specification/references/` |
| `ZERO/docs/inspirations/` | `ZERO/specification/inspirations/` |
| `ZERO/docs/ZERO-ITERATION.md` | `ZERO/ZERO-ITERATION.md` |

### 链接修改示例

```markdown
# 旧链接
[规范](./docs/standards/00.meta-01.core.md)

# 新链接
[规范](./specification/standards/00.meta-01.core.md)
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
   # 查找所有 ZERO/docs 的引用
   grep -r "ZERO/docs" .
   
   # 替换为新路径
   sed -i 's|ZERO/docs|ZERO/specification|g' file.txt
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
cat ZERO/specification/standards/00.meta-01.core.md

# 查看精炼版
cat ZERO/specification/condensed/00.meta-01.core.md

# 查看参考实现
cat ZERO/specification/references/admin-layout.md
```

### 在项目中引用 ZERO 规范

```markdown
# 在项目文档中引用 ZERO
[ZERO 元规范](../ZERO/specification/standards/00.meta-01.core.md)
[ZERO 快速参考](../ZERO/README.md)
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
   - 新增文档时使用 `specification/` 路径
   - 避免在 `docs/` 中添加新文件

### 对使用 ZERO 的项目

1. **更新 ZERO 后**
   - 确保项目文档正确引用 ZERO 规范
   - 测试所有链接

2. **文档引用**
   - 使用相对路径时注意目录结构
   - 考虑使用统一的规范引用模板

---

## 🔗 相关文档

- `ZERO/README.md` - ZERO 框架说明
- `ZERO/ZERO-ITERATION.md` - ZERO 迭代流程
- `ZERO/specification/standards/` - ZERO 规范集合

---

## ❓ FAQ

### Q: 为什么要改为 `specification/`？
A: 为了避免与项目中的 `docs/` 目录冲突，使用专有名称 `specification/` 清晰表示这是规范集合。

### Q: 旧链接还能用吗？
A: 旧链接可以通过 Git 历史访问，但建议更新为新路径以保持一致性。

### Q: 如何快速更新所有链接？
A: 使用 `sed` 或其他文本替换工具批量替换 `ZERO/docs` 为 `ZERO/specification`。

### Q: 这个变更对我的项目有影响吗？
A: 如果你的项目直接引用了 `ZERO/docs/` 的路径，需要更新为 `ZERO/specification/`。

---

**最后更新**：2026-04-12
**版本**：1.0.0

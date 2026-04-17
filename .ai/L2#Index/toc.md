# ZERO 框架规范 (ZERO Framework Specifications)

> **定位**：ZERO 框架的规范文档集合
> **版本**：v1.0.0
> **适用范围**：任意技术栈的 Web 项目

---

## 📋 快速导航

ZERO 是以文件夹路径为唯一主体的命名规范框架（路径为王）。

### 📂 目录说明

- **standards/** - 完整规范（20+ 文件）
  - 核心架构原则
  - 路径映射规范
  - API、数据库、前端、质量规范
  - 详细说明和多个例子

- **condensed/** - 精炼版本（100-150 行/文件）
  - 为 AI 优化的快速参考
  - ZERO 核心概念的总结
  - Token 使用更少

- **references/** - 参考实现
  - 管理后台布局
  - 组件实现
  - 最佳实践示例

- **inspirations/** - 灵感来源库
  - Claude-Code-Source 参考
  - 企业级项目经验

### 🗂️ 主题索引

#### 工具与开发流程

- **Hooks 与规范同步** - `09.tool-04.hooks.md`
  - Hook 配置规范（支持 hook 的 IDE）
  - 规范同步冲突检测流程（开发方法论级，适用所有环境）
  - 自动触发 vs 手动执行
  - 逐步纯化历史文档

- **脚本管理** - `09.tool-01.gogogo-sh.md`
  - gogogo.sh 统一入口脚本
  - 部署、开发、缓存管理

- **AI 记忆体系管理** - `09.tool-03.ai-gogogo.md`
  - gogogo.sh 8：IDE 映射管理（L1#项目概览 (Overview)/L2#规范索引 (Index)/L3#完整规范 (Standards) → 各 IDE）
  - gogogo.sh ai：AI 体系状态、Kiro specs 同步、L4#操作日志 (Changelog) 日志

- **AI 记忆体系架构** - `10.ai-memory-01.architecture.md`
  - 六层架构（L0#工作执行 (Execution) - L5#知识图谱 (Knowledge)）
  - 文档蒸馏与映射

- **六层架构命名规范** - `10.ai-memory-02.naming.md`
  - 六层架构文件命名规范
  - 各层命名方式和分类编号

- **六层架构官方命名对照表** - `10.ai-memory-03.six-layer-naming.md`
  - 中英文命名对照表
  - 文件夹和文档引用格式
  - 从七层迁移到六层的步骤

#### 工作流与集成

- **工作流集成** - `08.workflow-00.integration.md`
  - CI/CD 集成
  - Git 工作流
  - 部署流程
  - 自动化测试

### 🎯 核心概念

#### 路径为王 (Path is King)

文件夹路径是唯一主体，数据库表、API路由、后端类、权限点全部从路径自动推导：
开始
```
文件夹路径（唯一主体）
pages/admin/users/config/levels/
        ↓ 自动映射
数据库表：admin_users_config_levels
API路径：/api/admin/users/config/levels
后端类名：AdminUsersConfigLevels
权限标识：admin.users.config.levels
```

### 🤖 对 AI 的友好性

- ✅ 简洁的目录结构便于 LLM 理解
- ✅ condensed/ 版本为 AI 优化
- ✅ 清晰的规范便于 Agent 执行
- ✅ 支持所有主流 AI IDE

### 📚 了解更多

- [完整分析](../../STANDARDS-ANALYSIS.md)
- [迁移指南](../MIGRATION-GUIDE.md)
- [项目规范](../../rules/README.md)

---

**最后更新**：2026-04-16

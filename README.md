# ZERO - PathKing

> **定位**：以文件夹路径为唯一主体的命名规范框架（路径为王）
> **版本**：v1.0.0
> **适用场景**：任意技术栈的 Web 项目

---

## 🎯 核心理念

### 路径为王（Path is King）

**文件夹路径是唯一主体**，数据库表、API路由、后端类、权限点全部从路径自动推导：

```
文件夹路径（唯一主体）
pages/admin/users/config/levels/
        ↓ 自动映射
数据库表：admin_users_config_levels
API路径：/api/admin/users/config/levels
后端类名：AdminUsersConfigLevels
权限标识：admin.users.config.levels
```

### 设计哲学

1. **Evidence > assumptions** - 证据胜过假设
2. **Code > documentation** - 代码胜过文档
3. **Simple binary > complex hierarchy** - 简单二元规则胜过复杂多级优先级

### 命名哲学（AI 开发友好）

1. **完整描述 > 缩写简写** - `authentication.api.php` 而非 `auth.cmd.php`
2. **AI 友好 > 人类打字方便** - 命名可以长，但必须精准
3. **行业通用 > 项目特定** - 使用行业公认术语，避免自创缩写
4. **精准语义 > 模糊简称** - `processUserRegistration()` 而非 `process()`

详见：[04.quality-00.naming-philosophy.md](docs/standards/04.quality-00.naming-philosophy.md)

---

## 📁 文档结构

```
Zero/
├── README.md                           # 本文件（浓缩导航版）
├── go.sh                               # 统一入口脚本
├── go.lib.sh                           # 通用库
├── go.1.sh                             # 选项 1: 本地开发
├── go.2.sh                             # 选项 2: 部署
├── go.3.sh                             # 选项 3: 清缓存
└── docs/
    ├── ZERO-ITERATION.md              # ZERO 框架迭代流程（元文档）
    │
    ├── standards/                      # 框架基础规范
    │   ├── 00.meta-01.core.md         # 元规范
    │   ├── 01.arch-01.core.md         # 核心架构原则
    │   ├── 01.arch-02.structure.md    # 路径映射规范
    │   ├── 02.backend-01.api.md       # API设计规范
    │   ├── 02.backend-02.db-tables.md # 数据库表命名规范
    │   ├── 02.backend-03.db-fields.md # 数据库字段规范
    │   ├── 02.backend-04.db-manifest.md # 页面清单表规范
    │   ├── 03.frontend-01.structure.md # 文件命名规范
    │   ├── 04.quality-00.naming-philosophy.md # 命名哲学（AI友好）⭐新增
    │   ├── 04.quality-01.naming.md    # 命名规范
    │   ├── 05.biz-01.menu.md          # 侧边栏菜单规范
    │   ├── 06.quality-01.size.md      # 文件大小与拆分规范
    │   ├── 06.quality-02.git.md       # Git提交规范
    │   ├── 06.quality-03.error.md     # 错误处理规范
    │   ├── 06.quality-04.header.md    # 文件头注释规范
    │   ├── 09.tool-01.gosh.md         # go.sh 脚本规范
    │   └── 09.tool-02.deployignore.md # 部署排除规则规范
    │
    ├── references/                     # 组件/功能参考（具体实现）
    │   ├── README.md                  # 参考文档索引
    │   ├── admin-layout.md            # 管理后台 ABCD 布局
    │   ├── vanilla-spa.md             # 原生 SPA 实现参考
    │   ├── database-table-*.md        # 通用表格组件（8个文件）
    │   └── manifest-admin.md          # Manifest 管理页面
    │
    └── condensed/                      # 精炼版规范（100-150行/文件）
        └── ...
```

---

## 🔄 路径映射规则

| 源 | 目标 | 转换方法 | 举例 |
|---|------|---------|------|
| 文件夹路径 | 数据库表 | 下划线连接 | `admin_users_config_levels` |
| 文件夹路径 | API路径 | 加 `/api/` 前缀 | `/api/admin/users/config/levels` |
| 文件夹路径 | 类名 | 大驼峰连接 | `AdminUsersConfigLevels` |
| 文件夹路径 | 权限标识 | 点号连接 | `admin.users.config.levels` |

---

## 🗄️ 数据库规范

### 页面清单表（核心）

**表名**：`{系统前缀}_manifest_list`

这是"路径为王"架构的核心表，存储所有页面/功能模块的配置信息：

| 核心字段 | 说明 |
|---------|------|
| `path` | 文件夹路径（唯一主体） |
| `url` | 访问URL |
| `route` | 路由名称 |
| `shortName` | 菜单显示名称 |
| `icon` | 图标 |
| `sortOrder` | 排序 |
| `status` | 状态 |

**Fallback 策略**：无配置时使用默认值快速暴露问题
- `shortName` → 文件夹名
- `icon` → `help-circle`（问号）
- `sortOrder` → `-1`（排最前）

详见：[02.backend-04.db-manifest.md](docs/standards/02.backend-04.db-manifest.md)

### 侧边栏菜单

**文件系统优先**：目录存在即显示，数据库配置是增强不是必需。

```
文件系统扫描 → manifest_list 匹配 → 警告标记 → 缓存 → 渲染
```

| 状态 | 显示效果 |
|------|---------|
| 无数据库记录 | 显示目录名 + 红色警告 |
| 字段不完整 | 显示已有值 + 黄色警告（提示缺少哪些字段） |
| 配置完整 | 正常显示 |

**无硬编码默认值**：没有就是 null，前端根据 null 显示警告状态。

详见：[05.biz-01.menu.md](docs/standards/05.biz-01.menu.md)

### 表命名

```
{路径下划线连接}_{通用语义后缀}
```

| 后缀 | 含义 | 举例 |
|------|------|------|
| `list` | 主表 | `admin_users_list` |
| `config` | 配置表 | `admin_users_config_roles` |
| `log` | 日志表 | `admin_users_log_login` |

**规则**：通用语义后缀用**单数**，业务词汇用**复数**

### 表注释格式

```sql
'中文名称|功能说明'
-- 举例：'用户主表|存储用户基础信息'
```

### 字段注释格式

```sql
'序号|中文字段分类|中文字段名|详细说明[|是否显示]'
-- 举例：'1|核心|用户名|用于登录的唯一标识|1'
```

### 字段命名（三段式）

```
{表级前缀}_{语义分类}_{字段名}
```

举例：`base_profile_nickname`、`base_status_active`

---

## 📡 API规范（冒号语法）

**斜杠 `/` 仅用于真实目录，虚拟参数用冒号 `:`**

```bash
GET    /api/admin/users/list              # 列表
POST   /api/admin/users/list              # 创建
PUT    /api/admin/users/list:123          # 更新ID=123 ✅
DELETE /api/admin/users/list:456          # 删除ID=456 ✅
GET    /api/admin/users/list:export       # 导出 ✅

# ❌ 禁用（与文件路径混淆）
PUT    /api/admin/users/list/123
```

---

## 📋 命名规范速查

| 场景 | 风格 | 举例 |
|------|------|------|
| **目录路径** | **全小写（强制）** | `pages/admin/users/` |
| 文件名 | 点分命名 | `UsersList.view.html` |
| 变量/函数 | camelCase | `userName` |
| 类名 | PascalCase | `UserManager` |
| 常量 | UPPER_SNAKE | `MAX_COUNT` |
| CSS类 | kebab-case | `user-profile` |
| 数据库表 | 下划线 | `admin_users_config_levels` |
| 数据库字段 | 三段式 | `base_profile_nickname` |
| API路由 | 冒号语法 | `/list:export` |

### 文件点分命名

```
FeatureName.FileType.ext
```

| 类型 | 举例 |
|------|------|
| 视图 | `UsersList.view.html` |
| 逻辑 | `UsersList.logic.js` |
| 样式 | `UsersList.style.css` |
| API | `UsersList.api.php` |

**FeatureName 规则**：路径最后两级大驼峰组合
- `/admin/users/list/` → `UsersList`

---

## 📏 文件大小规范

| 级别 | 行数 |
|------|------|
| 推荐 | 300-500 |
| 上限 | 700 |
| 强制重构 | >800 |

**函数/方法**：推荐 10-40 行，上限 80 行

详见：[06.quality-01.size.md](docs/standards/06.quality-01.size.md)

---

## 📝 Git 提交规范

### Commit 格式

```
<type>(<scope>): <subject>
```

### 提交类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `docs` | 文档变更 |
| `refactor` | 重构 |
| `perf` | 性能优化 |

### 分支命名

| 类型 | 格式 |
|------|------|
| 功能 | `feature/<功能名>` |
| 修复 | `fix/<问题描述>` |
| 发布 | `release/<版本号>` |

详见：[06.quality-02.git.md](docs/standards/06.quality-02.git.md)

---

## ⚠️ 错误处理规范

### HTTP 状态码

| 状态码 | 含义 | 处理 |
|--------|------|------|
| 400 | 参数错误 | 显示错误信息 |
| 401 | 未认证 | 跳转登录 |
| 403 | 无权限 | 显示提示 |
| 422 | 验证失败 | 显示字段错误 |
| 500 | 服务器错误 | 显示通用错误 |

### 用户提示原则

- 用户能理解，避免技术术语
- 提供解决方案
- 不暴露敏感信息

详见：[06.quality-03.error.md](docs/standards/06.quality-03.error.md)

---

## 📄 文件头注释规范

**文件自包含文档化**：在文件开头用注释完整记录逻辑、思路、结构。

### 必需字段

| 字段 | 说明 |
|------|------|
| 【文件职责】 | 核心职责 |
| 【核心架构】 | 架构要点 |
| 【主要函数】 | 函数列表 |
| 【依赖关系】 | 依赖说明 |

### 同步规则

- 修改代码 → 更新注释
- 新增函数 → 更新【主要函数】

详见：[06.quality-04.header.md](docs/standards/06.quality-04.header.md)

---

## 🚀 go.sh 统一入口脚本

**统一入口**：一个命令搞定所有常用操作。

### 使用方式

```bash
./go.sh        # 交互式菜单
./go.sh 1      # 直接执行选项 1
```

### 选项编号

| 编号 | 用途 |
|------|------|
| 0 | 退出 |
| 1 | 本地开发（默认） |
| 2 | 部署 |
| 3 | 清缓存 |
| 4+ | 按需扩展 |

### 文件结构

```
go.sh          # 主入口
go.lib.sh      # 通用库
go.1.sh        # 选项 1
go.2.sh        # 选项 2
...
```

详见：[09.tool-01.gosh.md](docs/standards/09.tool-01.gosh.md)

---

## 🚨 零容忍规则

1. **目录路径必须全小写**
2. **API虚拟参数禁用斜杠**，必须用冒号
3. **文件超800行必须拆分**
4. **数据库通用语义后缀用单数**
5. **修改代码必须同步更新文件头注释**
6. **Commit 必须符合格式规范**

---

## 🎯 简单二元规则

```javascript
// ❌ 多级降级掩盖问题
const name = config?.shortName || config?.name || config?.title || folderName

// ✅ 简单二元，快速暴露问题
const name = config?.shortName || folderName
```

---

**最后更新**：2025-12-31

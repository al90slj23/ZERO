# manifest_list 核心表升级总结

> **升级日期**：2026-02-03
> **实践来源**：YYSYYF 项目 yys_manifest_list 表设计
> **文档版本**：v2.0.0

---

## 🎯 升级目标

将 `manifest_list` 从一个普通的页面配置表，升级为 **ZERO 框架的核心表**，为所有应用 ZERO 框架的项目提供坚固的路径基地。

---

## 📊 升级内容对比

### 架构地位提升

**升级前**：
- 定位：页面清单表
- 范围：主要用于 admin 管理后台
- 作用：存储页面配置信息

**升级后**：
- 定位：**ZERO 框架核心表**
- 范围：适用于所有需要路径管理的场景（admin/home/space/api 等）
- 作用：
  - 单一数据源（Single Source of Truth）
  - 路由、菜单、权限的唯一配置来源
  - 为整个应用提供一致的路径映射和配置管理

### 字段设计优化

#### 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `parent_path` | VARCHAR(255) | 父级路径，支持树形菜单结构 |
| `is_visible` | TINYINT(1) | 菜单可见性控制 |
| `is_menu` | TINYINT(1) | 是否作为菜单项 |
| `view_settings` | JSON | 页面级配置对象（权限、缓存等） |
| `source` | ENUM | 数据来源标识（database/filesystem） |
| `file_path` | VARCHAR(500) | 文件系统完整路径 |
| `deleted_at` | TIMESTAMP | 软删除支持 |

#### 字段重命名

| 旧字段名 | 新字段名 | 说明 |
|---------|---------|------|
| `url` | `path` | 统一使用 path 作为唯一主体 |
| `shortName` | `short_name` | 遵循下划线命名规范 |
| `sortOrder` | `sort_order` | 遵循下划线命名规范 |
| `vuePageComponent` | `component` | 简化命名 |

#### 移除字段

| 字段 | 原因 |
|------|------|
| `route` | 可从 path 自动推导，无需存储 |
| `briefName` | 简化设计，使用 short_name 即可 |
| `info`, `shortInfo`, `helpText` | 合并到 description |
| `color` | 移到 view_settings JSON 中 |
| `mappedPath` | 移到 view_settings JSON 中 |
| `supportingFiles` | 移到 view_settings JSON 中 |
| `metadata` | 改名为 view_settings，更明确 |

### 字段排序优化

**按查看/修改频率排序**（遵循规范 02.backend-03.db-fields）：

```
1. 核心标识字段（高频查看）
   id, path, parent_path

2. 展示信息字段（高频查看）
   name, short_name, icon, description

3. 路由配置字段（中频修改）
   component, redirect, is_external

4. 菜单控制字段（中频修改）
   sort_order, is_visible, is_menu

5. 扩展配置字段（低频查看）
   view_settings, source, file_path

6. 审计字段（低频查看）
   created_at, updated_at, deleted_at
```

---

## 🚀 新增功能

### 1. 树形菜单支持

通过 `parent_path` 字段构建树形菜单结构：

```sql
-- 顶级菜单
path = '/admin/yys'
parent_path = NULL

-- 二级菜单
path = '/admin/yys/manifest'
parent_path = '/admin/yys'

-- 三级菜单
path = '/admin/yys/manifest/lists'
parent_path = '/admin/yys/manifest'
```

### 2. 灵活的页面配置

通过 `view_settings` JSON 字段支持任意页面配置：

```json
{
  "requiresAuth": true,
  "keepAlive": false,
  "layout": "default",
  "permissions": ["admin.view"],
  "meta": {
    "title": "页面标题",
    "breadcrumb": ["首页", "系统", "视图"]
  }
}
```

### 3. 菜单可见性控制

- `is_visible=1`：显示在菜单中
- `is_visible=0`：隐藏菜单但路由可访问（如详情页）
- `is_menu=0`：仅作为路由，不显示在菜单（如 API 端点）

### 4. 文件系统同步机制

```bash
php artisan view:sync       # 扫描文件系统，同步到数据库
php artisan view:validate   # 验证数据库与文件系统一致性
php artisan view:fix        # 自动修复不一致问题
```

### 5. 软删除支持

使用 `deleted_at` 字段支持 Laravel 软删除：
- 删除目录时不物理删除记录
- 可恢复已删除的配置
- 保留历史数据用于审计

---

## 📝 文档升级

### 02.backend-04.db-manifest.md

**升级内容**：
- 文档版本：v1.0.0 → v2.0.0
- 新增"架构地位"章节，明确核心表定位
- 完整的字段设计说明（按频率分类）
- 详细的同步机制说明（零容忍规则）
- 4 个使用场景的完整代码示例
- 5 个常见问题与解决方案
- 实践案例：YYSYYF 项目经验总结

### README.md

**升级内容**：
- 强调 manifest_list 作为核心表的地位
- 突出"不仅限于 admin"的适用范围
- 新增三大核心功能说明
- 新增同步机制（零容忍）说明
- 添加 YYSYYF 实践案例

---

## 🎯 设计理念强化

### 1. 单一数据源（Single Source of Truth）

```
文件系统（Vue 页面）→ 数据库（manifest_list）→ 前端渲染（菜单/路由/页面）
     ↓                      ↓                           ↓
  开发时创建            artisan sync                动态加载配置
```

### 2. 简单二元规则

```javascript
// ✅ 简单二元规则（快速暴露问题）
const menuName = item.short_name || item.name

// ❌ 多级降级（掩盖配置问题）
const menuName = item.short_name || item.name || item.title || folderName
```

### 3. 零容忍规则

**文件变化后必须立即同步**：
```bash
# 1. 修改 Vue 文件
# 2. 立即同步（零容忍）
php artisan view:sync
# 3. 提交前验证
php artisan view:validate
```

---

## 📊 实践案例：YYSYYF 项目

### 表名
`yys_manifest_list`

### 规模
- 记录数：150+ 条
- 覆盖范围：8 个业务模块（yin/yue/sheng/yuan/yu/fang/yys/yyf）
- 菜单层级：3 级树形结构

### 关键特性
1. **树形菜单**：通过 `parent_path` 构建 3 级菜单
2. **动态路由**：前端路由完全由数据库驱动
3. **权限控制**：`view_settings.permissions` 控制页面访问
4. **缓存优化**：Redis 缓存 + 1 小时 TTL
5. **自动同步**：`view:sync` 命令自动扫描文件系统

### 成功经验
- 新增页面只需创建 Vue 文件 + 执行 `view:sync`
- 菜单调整只需修改数据库 + 刷新缓存
- 权限变更无需修改代码，只需更新 `view_settings`

---

## ✅ 升级检查清单

### 表设计
- [x] 表名符合 `{系统前缀}_manifest_list` 格式
- [x] `path` 字段有唯一索引
- [x] `parent_path` 字段有普通索引
- [x] 字段注释符合 `序号|分类|名称|说明|显示` 格式
- [x] 字段按查看/修改频率排序
- [x] 有软删除支持（`deleted_at` 字段）

### 同步机制
- [x] 有 `view:sync` 命令扫描文件系统
- [x] 有 `view:validate` 命令验证一致性
- [x] 有 `view:fix` 命令自动修复
- [x] 文件变化后会自动清除缓存

### 文档
- [x] 规范文档升级到 v2.0.0
- [x] README.md 突出核心表地位
- [x] 添加实践案例说明
- [x] 添加使用场景代码示例
- [x] 添加常见问题与解决方案

---

## 🔄 迁移指南

### 从旧版本迁移

如果你的项目使用了旧版本的 manifest 表，可以按以下步骤迁移：

#### 1. 备份数据

```sql
CREATE TABLE {prefix}_manifest_list_backup AS 
SELECT * FROM {prefix}_manifest_list;
```

#### 2. 添加新字段

```sql
ALTER TABLE {prefix}_manifest_list
  ADD COLUMN parent_path VARCHAR(255) DEFAULT NULL AFTER path,
  ADD COLUMN is_visible TINYINT(1) NOT NULL DEFAULT 1 AFTER sort_order,
  ADD COLUMN is_menu TINYINT(1) NOT NULL DEFAULT 1 AFTER is_visible,
  ADD COLUMN view_settings JSON DEFAULT NULL AFTER is_menu,
  ADD COLUMN source ENUM('database','filesystem') DEFAULT 'database' AFTER view_settings,
  ADD COLUMN file_path VARCHAR(500) DEFAULT NULL AFTER source,
  ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL AFTER updated_at;
```

#### 3. 重命名字段

```sql
ALTER TABLE {prefix}_manifest_list
  CHANGE COLUMN url path VARCHAR(255) NOT NULL,
  CHANGE COLUMN shortName short_name VARCHAR(50) DEFAULT NULL,
  CHANGE COLUMN sortOrder sort_order INT NOT NULL DEFAULT 1,
  CHANGE COLUMN vuePageComponent component VARCHAR(255) DEFAULT NULL;
```

#### 4. 删除废弃字段

```sql
ALTER TABLE {prefix}_manifest_list
  DROP COLUMN route,
  DROP COLUMN briefName,
  DROP COLUMN info,
  DROP COLUMN shortInfo,
  DROP COLUMN helpText,
  DROP COLUMN color,
  DROP COLUMN mappedPath,
  DROP COLUMN supportingFiles,
  DROP COLUMN metadata;
```

#### 5. 添加索引

```sql
ALTER TABLE {prefix}_manifest_list
  ADD INDEX idx_parent_path (parent_path),
  ADD INDEX idx_is_visible (is_visible),
  ADD INDEX idx_is_menu (is_menu),
  ADD INDEX idx_deleted_at (deleted_at);
```

#### 6. 数据迁移

```sql
-- 根据 path 推导 parent_path
UPDATE {prefix}_manifest_list
SET parent_path = SUBSTRING(path, 1, LENGTH(path) - LENGTH(SUBSTRING_INDEX(path, '/', -1)) - 1)
WHERE path LIKE '%/%/%';

-- 顶级菜单的 parent_path 设为 NULL
UPDATE {prefix}_manifest_list
SET parent_path = NULL
WHERE path NOT LIKE '%/%/%';
```

#### 7. 执行同步

```bash
php artisan view:sync
php artisan view:validate
```

---

## 🎉 总结

通过这次升级，`manifest_list` 从一个普通的页面配置表，升级为 **ZERO 框架的核心表**，具备以下特点：

1. **架构地位明确**：ZERO 框架的配置中枢
2. **适用范围广泛**：不仅限于 admin，适用于所有路径管理场景
3. **功能完善**：支持树形菜单、动态路由、权限控制、缓存优化
4. **设计规范**：字段按频率排序，三段式命名，简单二元规则
5. **实践验证**：基于 YYSYYF 项目 150+ 条记录的成功实践

这张表将成为所有应用 ZERO 框架项目的**坚固路径基地**，为整个应用提供一致的路径映射和配置管理。

---

**升级完成日期**：2026-02-03
**GitHub 提交**：feat: 升级 manifest_list 为 ZERO 核心表，整合 YYSYYF 实践经验

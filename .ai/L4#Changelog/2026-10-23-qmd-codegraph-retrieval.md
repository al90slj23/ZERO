# ZERO v2.1：L5 定位与 QMD / CodeGraph 适配

> 日期：2026-10-23
> 类型：decision

## 背景

L5 最初希望由知识图谱工具承载，原 README 明确提到图数据库和 MCP。后续规范却出现把理由记入“L5 文档”的要求，导致采用项目把本层作为手工维护的知识文档库。QMD 和 CodeGraph 的引入需要同时澄清这项歧义。

## 决策

- 发布定义为 ZERO v2.1.0，六层物理路径继续使用原有格式。
- L5 正式中文名称改为“知识检索与关联”，目录 `.ai/L5#Knowledge/` 保存接入与边界说明。
- 文档事实与执行资料归属 L0-L4；QMD 派生文档检索索引，CodeGraph 派生源码关系图。L5 不承担第二份事实保存职责。
- 移除 L5 作为当前规范的独立蒸馏来源和固定必读文档层的含义；查询结果需要追溯其原始来源。
- 两者不提供完整的通用实体/事件/时态图，未来有明确需求时再增加图谱适配器。
- 只维护 `.ai` 内的知识源资料；配置、数据库和模型缓存全部在 `.ai/L5#Knowledge/.generated/` 自动构建与更新。QMD 通过命名索引与目录环境变量隔离；CodeGraph 根 `.codegraph` 仅作自动软链。
- MCP 启动和 Agent 任务收尾触发自动补齐；一次性合并客户端连接入口，避免 CodeGraph installer 改写 ZERO 的 L1 映射。不要求用户每次手动刷新。
- 为已有 L5 文档、图数据库和引用提供归位与保留流程，不改写旧 L4 历史日志。

## 交付与验证边界

本次交付修改 ZERO 模板、当前规范、入口、迁移指南和本地工作流。真实项目的索引质量与 MCP 连通性需在该项目安装 CLI 后按新规范验收；本次不以模拟 CLI 检查代替真实检索验收。

## 来源

- [QMD 官方文档](https://github.com/tobi/qmd)
- [CodeGraph 官方文档](https://github.com/colbymchenry/codegraph)
- [CodeGraph 索引与 watcher](https://github.com/colbymchenry/codegraph/blob/main/site/src/content/docs/guides/indexing.md)

模板阶段验证：Bash 语法、ShellCheck、hook JSON、新增文档链接和 mock CLI 调度检查通过。mock 覆盖生成目录、根软链、旧库保留、配置重建、失败传播与 MCP stdout。官方源码核对基线为 QMD 2.8.3、CodeGraph 1.6.2；该阶段未安装真实 CLI。

同日 ALV 采用项目接入补充：CodeGraph 软链通过真实 CLI、MCP 和文件变更 watcher 验证；双 MCP 客户端并发查询共用同一 daemon，断开其一不影响另一个。负责人选择标准共享模式，允许工具自动维护用户目录进程登记与临时 socket，项目知识、模型和索引继续全部保存在 `.ai`。QMD 读取不再刷新全库；启动后台补齐、收尾互斥等待，避免清查询缓存或阻塞 MCP 握手。

ALV QMD 后续真实验收：1,034 份文档、待嵌入 0，源文档新增/修改/删除同步、中文语义检索、自动扩展与重排混合查询、MCP 均通过。中文宿主写入边界问题首条命中当前最高优先级规范。适配器 27 项并发/失败边界 mock 通过；采用项目仍需自行验证其语料与运行环境。

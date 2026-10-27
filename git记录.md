# Git 提交记录

## [2026-10-27 11:24] chore: 移除运行时数据跟踪并脱敏文档密码

### 功能点简述
- 将误入版本库的 Docker 运行时数据与 .DS_Store 移出 Git 跟踪（本地文件保留），并在 .gitignore 中固化忽略规则；对《账户功能说明.md》中测试账号密码脱敏，消除凭据暴露风险。

### 变更/新增代码
| 文件 | 类型（新增/修改/删除） | 说明 |
|------|----------------------|------|
| .gitignore | 修改 | 新增 `.DS_Store` 与 `docker/mysql/data/`、`docker/redis_data/`、`docker/minio_data/` 忽略规则 |
| .DS_Store | 删除（索引） | macOS 桌面元数据移出版本库 |
| docker/mysql/data/**（190 个文件） | 删除（索引） | MySQL 运行时数据（binlog/ibdata/performance_schema 等）移出版本库，本地保留 |
| docker/minio_data/**（26 个文件） | 删除（索引） | MinIO 运行时元数据移出版本库，本地保留 |
| app/docs/账户功能说明.md | 修改 | 测试账号密码由 `Yuwen...` 脱敏为 `********`（表格与 JSON 示例两处） |

### 影响范围
- 涉及模块：仓库卫生（.gitignore / 运行时数据）与前端文档；后端业务代码零改动。
- 潜在风险：其他协作者拉取后，本地 docker 运行时数据文件仍在其磁盘上，但 Git 不再跟踪；后续 `docker compose` 产生的数据不会再进入提交。
- 回归建议：确认 `docker compose ps` 与 MySQL/MinIO 服务运行正常（本地文件未动，理论无影响）；全局搜索确认文档中无明文密码残留。

### 提交记录
- 分支：main
- Commit：551bd0e

## [2026-10-27 11:18] 前端代码提交：品牌名全局替换辰光为fy，新增项目工程结构说明文档

### 功能点简述
- 将前端品牌名「辰光」全局替换为「fy」（覆盖 app/README.md、app/docs 8 篇文档、app/src 6 个源码文件），并新增根目录《项目工程目录.md》工程结构说明文档；其中《账户功能说明.md》同步补充后端登录/验证码/当前用户接口联调说明。

### 变更/新增代码
| 文件 | 类型（新增/修改/删除） | 说明 |
|------|----------------------|------|
| 项目工程目录.md | 新增 | 项目完整工程结构说明：后端 FastAPI 分层架构、前端 React 模块、Alembic 迁移、Docker 基础设施、辅助脚本等 |
| app/README.md | 修改 | 品牌名 辰光→fy（标题） |
| app/docs/00-架构总览.md | 修改 | 品牌名 辰光→fy（产品定位、导航树） |
| app/docs/04-Prompt管理.md | 修改 | 品牌名 辰光→fy（示例文本） |
| app/docs/05-知识库管理.md | 修改 | 品牌名 辰光→fy（示例文本） |
| app/docs/06-工具管理.md | 修改 | 品牌名 辰光→fy（示例文本） |
| app/docs/09-系统管理.md | 修改 | 品牌名 辰光→fy（默认系统名称） |
| app/docs/布局设计说明.md | 修改 | 品牌名 辰光→fy（Logo 与产品名称） |
| app/docs/知识库文档管理使用指南.md | 修改 | 品牌名 辰光→fy（功能概述） |
| app/docs/账户功能说明.md | 修改 | 品牌名替换；新增后端登录/验证码/当前用户接口文档、已验证接口清单 |
| app/src/layouts/DashboardLayout.tsx | 修改 | 侧边栏品牌名 辰光 Agent→fy Agent |
| app/src/pages/Login.tsx | 修改 | 登录页标题与版权文案 辰光→fy |
| app/src/pages/Profile.tsx | 修改 | 个人简介文案 辰光→fy |
| app/src/pages/agent/Test.tsx | 修改 | 测试页示例文案 辰光→fy |
| app/src/services/mock/data/knowledge-fixed.ts | 修改 | Mock 知识库片段文案 辰光→fy |
| app/src/services/mock/data/system.ts | 修改 | 系统设置 Mock siteName 辰光→fy |

### 影响范围
- 涉及模块：前端 app/（README、docs 文档、layouts、pages、services/mock）；根目录新增工程结构文档。纯文案与文档变更，不涉及业务逻辑与接口行为。
- 潜在风险：《账户功能说明.md》中记录了本地测试账号的用户名与密码，若仓库对外公开存在凭据暴露风险（当前为本地开发测试账号，风险可控，建议后续将密码移除或打码）。
- 回归建议：全局搜索「辰光」确认无残留；目测检查登录页、侧边栏、个人资料页的品牌展示；无需后端回归。

### 提交记录
- 分支：main
- Commit：1a28f6c20188db4138aefbbb2dfd07651c06561c

# 03 · 按 Git 提交的项目进度

> 数据来源：`git log`（共 7 个提交）。时间线为 2026-08-26 → 2026-09-15。
> 说明：其中 45b5164 / 3c5fdd9 / f17812e 三个提交只动了 MinIO 运行时数据（容器自写），无业务代码变化。

## 时间线总览
| # | Commit | 日期 | 主题 | 业务价值 |
|---|--------|------|------|----------|
| 1 | `1b27774` | 2026-08-26 | Initial commit | 仓库初始化（README/.gitignore） |
| 2 | `69c6fa5` | 2026-08-30 | 基础架构搭建 | 容器化 + 项目骨架 + 用户模块 + 迁移 |
| 3 | `45b5164` | 2026-08-30 | ‘ | 仅 MinIO 数据变动（无代码） |
| 4 | `3c5fdd9` | 2026-08-30 | 。 | 仅 MinIO 数据变动（无代码） |
| 5 | `f17812e` | 2026-08-30 | 。 | 仅 MinIO 数据变动（无代码） |
| 6 | `1abb2b0` | 2026-08-31 | 更新依赖 | requirements 增补（captcha 等） |
| 7 | `c63d6be` | 2026-09-15 | 验证码接口 | Redis 接入 + 图形验证码模块 |

---

## 里程碑 M1 · 初始化（commit `1b27774`，2026-08-26）
- 建立 Git 仓库、README（定位“企业内部 Agent 平台”）、`.gitignore`。
- 进度意义：确定项目方向与版本管理基线。

## 里程碑 M2 · 基础架构搭建（commit `69c6fa5`，2026-08-30）★ 核心
一次性落地了可运行的工程底座，是提交量与技术含量最高的一次：

- **基础设施容器化**：`docker-compose` 拉起 MySQL 8.4 / Redis / MinIO，统一网络 `app-network`、数据卷持久化、端口与密码约定。
- **应用骨架**：`src/main.py` 应用工厂 + lifespan；`core/`（config、base_model、base_schema、base_repository、exceptions、logger）；`infra/`（异步 DB、Redis 占位）；日志中间件。
- **异步数据层**：SQLAlchemy 2.0 async engine + 连接池 + `get_db` 事务依赖。
- **用户模块闭环**：model/schema/repository/service/api 五件套，提供建用户、查用户、列表三个接口。
- **数据库迁移**：alembic.ini + 异步 `env.py` + 前两个版本（init、建 users 表）。
- 进度意义：从 0 到“分层清晰、可启动、可 CRUD、可迁移”的后端骨架。

## 里程碑 M3 · 依赖更新（commit `1abb2b0`，2026-08-31）
- 增补依赖（为验证码图片生成、PyJWT/bcrypt、sentry 等做准备）。
- 进度意义：为下一阶段安全/认证能力铺好依赖。

## 里程碑 M4 · 验证码接口（commit `c63d6be`，2026-09-15）★ 最新
- **Redis 正式接入**：`infra/redis_cache.py` 模块级异步连接池 + `get_redis_client` 依赖。
- **验证码模块上线**：`GET /api/v1/captcha`（生成图片+base64+uuid，存 Redis 5 分钟）、`POST /api/v1/captcha`（校验，大小写不敏感、一次性删除）。
- 注册到 main 路由；异常码 10001（不存在/过期）、10002（错误）。
- 同期迁移：users 表新增 `is_superuser` 字段（版本 `6379c3290c7b`）。
- 进度意义：引入第一个“无状态服务 + Redis 有状态存储”的安全类能力，为登录防爆破做前置。

---

## 阶段划分（可直接写进周报/简历）
- **阶段一（8/26–8/31）地基期**：容器化 + 分层骨架 + 异步数据访问 + 用户 CRUD + 迁移体系。
- **阶段二（9/15– ）安全期（进行中）**：验证码完成；JWT/bcrypt 工具就绪；**下一步**实现 `/auth/login` 与登录态依赖。

## 下一步建议（按优先级）
1. 实现 `POST /api/v1/auth/login`：验证码校验 → 账号密码校验（接入 `password_utils`）→ 更新 `last_login_at` → `encode_jwt` 签发。
2. 新增 `get_current_user` 依赖：解析 Bearer Token → 加载用户 → 保护写接口。
3. 修复安全/规范问题（详见 04 文档），补齐 `.gitignore` 对 `docker/*_data`、`.env` 的忽略。
4. 为 user/captcha/auth 补 pytest + httpx.AsyncClient 异步接口测试。

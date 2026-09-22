# 企业内部 Agent 平台 — 项目进度与面试复盘

> 本文档目录独立于源码，仅用于记录项目进度与面试准备，**不改动任何业务代码**。
> 技术栈：FastAPI 0.135 · SQLAlchemy 2.0（async）· Alembic · MySQL 8.4 · Redis · Pydantic v2 · loguru · Docker Compose · PyJWT · bcrypt

## 目录
- [01 · 架构与目录结构分析](./01-architecture.md)
- [02 · 功能要点、难点与设计方法论](./02-features-methodology.md)
- [03 · 按 Git 提交的项目进度](./03-git-progress.md)
- [04 · 面试官视角：亮点、风险与问答清单](./04-interview-prep.md)

## 一句话项目定位
一个基于 **FastAPI 异步 + 分层 + 模块化（DDD-lite）** 的企业内部 Agent 平台后端骨架，
当前已完成：基础设施容器化、异步数据访问层、统一配置/日志/异常/响应规范、用户模块、图形验证码模块；
认证（JWT 登录）模块为进行中（脚手架已就位，登录接口尚未实现）。

## 当前完成度概览
| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 容器化基础设施（MySQL/Redis/MinIO） | ✅ 完成 | `docker/docker-compose.yaml` |
| 配置中心（.env + pydantic-settings 单例） | ✅ 完成 | `src/core/config.py` |
| 异步 DB 引擎/会话/事务依赖 | ✅ 完成 | `src/infra/database.py` |
| Redis 异步连接池 | ✅ 完成 | `src/infra/redis_cache.py` |
| 分层基类（Model / Repository / Schema） | ✅ 完成 | `src/core/` |
| 统一响应体 + 全局异常处理 | ✅ 完成 | `base_schema.py` / `exceptions.py` |
| 日志（控制台+文件轮转）+ 请求日志中间件 | ✅ 完成 | `logger.py` / `middlewares/logging.py` |
| 数据库迁移 Alembic（含异步 env） | ✅ 完成 | `alembic/` |
| 用户模块 CRUD（api/service/repository/model/schema） | ✅ 完成 | `src/modules/user/` |
| 图形验证码（生成/存储/校验） | ✅ 完成 | `src/modules/captcha/` |
| JWT / bcrypt 工具 | ⚠️ 工具就绪 | `src/utils/`，但未接入登录流程 |
| 认证登录接口 | 🚧 进行中 | `src/modules/auth/` 仅脚手架 |
| 单元测试 | ⚠️ 占位 | `test/test_sample.py` 仅示例 |

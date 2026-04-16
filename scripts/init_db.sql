-- 初始化数据库脚本
-- 此脚本会在 PostgreSQL 容器启动时自动执行

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 可以在这里添加初始数据
-- 例如：创建一个默认管理员用户等

-- 注释：实际的数据库表结构由 SQLAlchemy ORM 自动创建
-- 生产环境建议使用 Alembic 进行数据库迁移

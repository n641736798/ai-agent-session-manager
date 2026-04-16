# AI Agent 会话管理系统

一个基于 FastAPI 的 AI Agent 会话管理系统，支持用户认证、会话管理、对话历史缓存和 AI 推理模拟。

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0 (异步)
- **缓存**: Redis 7
- **认证**: JWT Token
- **任务队列**: Celery
- **容器化**: Docker + Docker Compose
- **日志**: Loguru

## 项目结构

```
fastapi-ai-service/
├── app/                      # 应用代码
│   ├── api/                  # API层
│   │   └── v1/
│   │       ├── dependencies/ # 依赖注入
│   │       ├── endpoints/    # API端点
│   │       └── router.py     # 路由聚合
│   ├── core/                 # 核心组件
│   │   ├── exceptions.py     # 自定义异常
│   │   └── middleware.py     # 中间件
│   ├── models/               # ORM模型
│   ├── schemas/              # Pydantic模型
│   ├── services/             # 业务服务
│   ├── tasks/                # 异步任务
│   ├── utils/                # 工具模块
│   ├── config.py             # 配置管理
│   ├── database.py           # 数据库连接
│   ├── main.py               # 应用入口
│   └── redis_client.py       # Redis客户端
├── scripts/                  # 脚本文件
├── tests/                    # 测试代码
├── docker-compose.yml        # 容器编排
├── Dockerfile                # 应用镜像
└── requirements.txt          # Python依赖
```

## 快速开始

### 1. 环境准备

确保已安装：
- Docker
- Docker Compose

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的环境变量：

```env
SECRET_KEY=your-secret-key-here-must-be-at-least-32-characters-long
```

### 3. 启动服务

```bash
docker-compose up -d
```

服务启动后：
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 4. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### 5. 停止服务

```bash
docker-compose down

# 删除数据卷（谨慎使用）
docker-compose down -v
```

## API 接口

### 健康检查

```http
GET /health
```

### 用户接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/users/register` | 用户注册 | 否 |
| POST | `/api/v1/users/login` | 用户登录 | 否 |
| GET | `/api/v1/users/me` | 获取当前用户 | 是 |
| PUT | `/api/v1/users/me` | 更新当前用户 | 是 |

### 会话接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/sessions` | 创建会话 | 是 |
| GET | `/api/v1/sessions` | 获取会话列表 | 是 |
| GET | `/api/v1/sessions/{session_id}` | 获取会话详情 | 是 |
| POST | `/api/v1/sessions/{session_id}/messages` | 发送消息 | 是 |
| DELETE | `/api/v1/sessions/{session_id}` | 删除会话 | 是 |

## 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 3. 创建会话

```bash
curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "新对话"
  }'
```

### 4. 发送消息

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/{session_id}/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "role": "user",
    "content": "你好"
  }'
```

## 本地开发

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动依赖服务

```bash
docker-compose up -d postgres redis
```

### 4. 运行应用

```bash
python -m app.main
```

或

```bash
uvicorn app.main:app --reload
```

### 5. 运行测试

```bash
pytest
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | AI Agent Service | 应用名称 |
| `APP_VERSION` | 1.0.0 | 应用版本 |
| `DEBUG` | false | 调试模式 |
| `SECRET_KEY` | - | JWT密钥（必填） |
| `DATABASE_URL` | postgresql+asyncpg://... | 数据库连接URL |
| `REDIS_URL` | redis://localhost:6379/0 | Redis连接URL |
| `SESSION_TTL` | 3600 | 会话缓存时间（秒） |
| `AI_MODEL` | gpt-3.5-turbo | AI模型名称 |

## 架构设计

### 数据流

1. **用户创建会话**
   - 用户调用 `POST /sessions`
   - 认证中间件验证JWT
   - SessionService 写入 PostgreSQL
   - 缓存会话元数据到 Redis

2. **用户发送消息**
   - 用户调用 `POST /sessions/{id}/messages`
   - SessionService 保存用户消息
   - AIService 生成 AI 响应
   - 保存 AI 响应到数据库
   - 返回完整会话

### 缓存策略

- **会话元数据**: `session:meta:{session_id}` - TTL 1小时
- **会话完整数据**: `session:full:{session_id}` - TTL 1小时
- **AI最后响应**: `session:last_response:{session_id}` - TTL 5分钟

## 生产部署

### 1. 修改配置

- 设置强密码的 `SECRET_KEY`
- 关闭 `DEBUG` 模式
- 配置生产级数据库和Redis
- 启用 HTTPS

### 2. 使用生产级服务器

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

或使用 Gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. 数据库迁移

生产环境建议使用 Alembic 进行数据库迁移：

```bash
# 初始化 Alembic
alembic init alembic

# 创建迁移脚本
alembic revision --autogenerate -m "initial migration"

# 执行迁移
alembic upgrade head
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系维护者。

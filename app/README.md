# app 目录结构详解

本文档详细解释 AI Agent 会话管理系统中 `app` 目录的组织结构和各模块的作用。

## 目录概览

```
app/
├── __init__.py                 # 包初始化
├── main.py                     # FastAPI 应用入口
├── config.py                   # 配置管理
├── database.py                 # 数据库连接
├── redis_client.py             # Redis 客户端
├── api/                        # API 层（路由和端点）
│   ├── __init__.py
│   └── v1/                     # API 版本 1
│       ├── __init__.py
│       ├── router.py           # 路由聚合
│       ├── dependencies/       # 依赖注入
│       │   ├── __init__.py
│       │   └── auth.py         # 认证逻辑
│       └── endpoints/          # API 端点
│           ├── __init__.py
│           ├── users.py        # 用户相关接口
│           └── sessions.py     # 会话相关接口
├── core/                       # 核心组件
│   ├── __init__.py
│   ├── exceptions.py           # 自定义异常
│   └── middleware.py           # 中间件
├── models/                     # 数据模型层（ORM）
│   ├── __init__.py
│   └── session.py              # User 和 Session 模型
├── schemas/                    # Pydantic 模型（数据验证）
│   ├── __init__.py
│   ├── user.py                 # 用户 Schema
│   └── session.py              # 会话 Schema
├── services/                   # 业务服务层
│   ├── __init__.py
│   ├── session_service.py      # 会话业务逻辑
│   └── ai_service.py           # AI 服务模拟
├── tasks/                      # 异步任务
│   ├── __init__.py
│   └── ai_tasks.py             # Celery 任务
└── utils/                      # 工具模块
    ├── __init__.py
    └── logger.py               # 日志配置
```

---

## 核心文件详解

### 1. main.py - FastAPI 应用入口

**作用**：应用程序的启动入口，负责组装所有组件。

**关键功能**：
- 创建 FastAPI 应用实例
- 注册中间件（CORS、日志、请求ID）
- 注册异常处理器
- 注册 API 路由
- 应用生命周期管理（启动/关闭）

**生命周期**：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：配置日志、连接 Redis、初始化数据库
    setup_logging()
    await redis_client.connect()
    await init_db()
    
    yield  # 应用运行期间
    
    # 关闭时：断开 Redis 连接
    await redis_client.disconnect()
```

---

### 2. config.py - 配置管理

**作用**：集中管理应用的所有配置项。

**技术**：使用 Pydantic Settings 从环境变量加载配置

**主要配置**：
- 应用配置：名称、版本、调试模式
- 数据库配置：连接 URL、连接池大小
- Redis 配置：连接 URL、最大连接数
- 会话配置：TTL（过期时间）
- AI 服务配置：模型名称、API 密钥、超时时间

**使用方式**：
```python
from app.config import settings

# 访问配置
db_url = settings.DATABASE_URL
secret = settings.SECRET_KEY
```

---

### 3. database.py - 数据库连接

**作用**：管理数据库连接和会话。

**技术**：SQLAlchemy 2.0 异步模式

**核心组件**：
- `engine`：数据库引擎（支持 SQLite 和 PostgreSQL）
- `AsyncSessionLocal`：异步会话工厂
- `Base`：ORM 模型基类
- `get_db()`：依赖注入函数，用于获取数据库会话
- `init_db()`：初始化数据库（创建所有表）

**使用示例**：
```python
from app.database import get_db

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # 使用 db 进行数据库操作
    pass
```

---

### 4. redis_client.py - Redis 客户端

**作用**：提供 Redis 连接和数据操作。

**特点**：单例模式，全局共享连接池

**核心方法**：
- `connect()`：建立连接池
- `disconnect()`：关闭连接
- `get(key)`：获取值（自动 JSON 反序列化）
- `set(key, value, ttl)`：设置值（自动 JSON 序列化）
- `delete(key)`：删除键
- `exists(key)`：检查键是否存在

**使用示例**：
```python
from app.redis_client import redis_client

# 设置缓存
await redis_client.set("user:1", {"name": "张三"}, ttl=3600)

# 获取缓存
user = await redis_client.get("user:1")
```

---

## API 层 (api/)

### router.py - 路由聚合

**作用**：整合所有 API 端点路由。

```python
api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
```

### dependencies/auth.py - 认证依赖

**作用**：JWT Token 验证和用户认证。

**核心函数**：
- `get_current_user()`：从请求头解析 JWT，获取当前用户
- `get_current_active_user()`：获取当前活跃用户（可扩展检查用户状态）

**使用方式**：
```python
from app.api.v1.dependencies.auth import get_current_user

@app.get("/me")
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
```

### endpoints/users.py - 用户接口

**端点列表**：

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/register` | 用户注册 | 否 |
| POST | `/login` | 用户登录（返回 JWT） | 否 |
| GET | `/me` | 获取当前用户信息 | 是 |
| PUT | `/me` | 更新当前用户信息 | 是 |

### endpoints/sessions.py - 会话接口

**端点列表**：

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/` | 创建会话 | 是 |
| GET | `/` | 获取会话列表 | 是 |
| GET | `/{session_id}` | 获取会话详情 | 是 |
| POST | `/{session_id}/messages` | 发送消息 | 是 |
| DELETE | `/{session_id}` | 删除会话 | 是 |

---

## 核心组件 (core/)

### exceptions.py - 自定义异常

**异常类层次**：

```
AIServiceException (基类)
├── SessionNotFoundException (404)
├── AuthenticationException (401)
└── RateLimitException (429)
```

**功能**：
- 定义业务异常
- 统一异常响应格式
- 全局异常处理器

### middleware.py - 中间件

**中间件列表**：

1. **CORSMiddleware**：跨域资源共享
   - 允许前端从不同域名访问 API

2. **RequestIDMiddleware**：请求追踪
   - 为每个请求生成唯一 ID
   - 记录请求处理时间
   - 添加响应头：`X-Request-ID`, `X-Process-Time`

3. **LoggingMiddleware**：日志记录
   - 记录请求方法、URL
   - 记录响应状态码

---

## 数据层

### models/session.py - ORM 模型

**User 模型**：
```python
class User(Base):
    id: int                    # 主键
    username: str              # 用户名（唯一）
    email: str                 # 邮箱（唯一）
    hashed_password: str       # 密码哈希
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    sessions: List[Session]    # 关联会话（一对多）
```

**Session 模型**：
```python
class Session(Base):
    id: int                    # 主键
    session_id: str            # 业务 UUID（唯一）
    user_id: int               # 外键（关联 User）
    title: str                 # 会话标题
    messages: JSON             # 对话历史（JSON 数组）
    meta_data: JSON            # 扩展元数据
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    user: User                 # 关联用户（多对一）
```

### schemas/ - Pydantic 模型

**作用**：数据验证和序列化

**user.py**：
- `UserCreate`：创建用户（username, email, password）
- `UserResponse`：用户响应（id, username, email, created_at）

**session.py**：
- `Message`：对话消息（role, content, timestamp）
- `SessionBase`：基础字段（title, meta_data）
- `SessionCreate`：创建会话
- `SessionUpdate`：更新会话
- `SessionResponse`：完整会话响应

---

## 业务服务层 (services/)

### session_service.py - 会话服务

**作用**：处理会话相关的业务逻辑。

**核心方法**：

| 方法 | 功能 |
|------|------|
| `create_session()` | 创建新会话，缓存元数据到 Redis |
| `get_session()` | 获取会话（优先从缓存读取） |
| `add_message()` | 添加消息到会话，使缓存失效 |
| `list_user_sessions()` | 获取用户的会话列表 |
| `delete_session()` | 删除会话，清理缓存 |

**设计模式**：依赖注入
```python
class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db  # 通过构造函数注入数据库会话
```

### ai_service.py - AI 服务

**作用**：模拟 AI 推理（实际应调用 OpenAI/Anthropic 等 API）。

**核心方法**：

| 方法 | 功能 |
|------|------|
| `generate_response()` | 生成 AI 响应（模拟 1.5s 延迟） |
| `stream_response()` | 流式生成响应（用于 SSE） |

**响应逻辑**：
- 包含"你好/hello" → 问候语
- 包含"天气" → 无法查询提示
- 其他 → 默认响应模板

**全局实例**：`ai_service = AIService()`

---

## 异步任务 (tasks/)

### ai_tasks.py - Celery 任务

**作用**：处理耗时的 AI 推理任务。

**配置**：
- Broker：Redis
- Backend：Redis
- 序列化：JSON

**任务**：
```python
@celery_app.task(bind=True, max_retries=3)
def process_ai_inference(self, session_id: str, message: str, history: list):
    """
    异步 AI 推理任务
    - 模拟处理延迟（2秒）
    - 支持最多 3 次重试
    """
```

**使用场景**：
- 长时间运行的 AI 推理
- 批量处理任务
- 定时任务

---

## 工具模块 (utils/)

### logger.py - 日志配置

**作用**：配置应用日志输出。

**技术**：Loguru（替代标准 logging）

**输出目标**：
1. **控制台**：彩色输出，开发环境 DEBUG 级别
2. **文件**（生产环境）：`logs/app.log`，按大小轮转（10MB），保留 30 天

**日志格式**：
```
2024-01-01 12:00:00 | INFO | module:function:line | 消息内容
```

---

## 数据流示例

### 用户创建会话流程

```
1. 用户 → POST /api/v1/sessions
2. auth.py → 验证 JWT Token
3. sessions.py → 调用 SessionService.create_session()
4. session_service.py → 
   - 写入 PostgreSQL（Session 表）
   - 缓存元数据到 Redis
5. 返回 SessionResponse
```

### 用户发送消息流程

```
1. 用户 → POST /api/v1/sessions/{id}/messages
2. sessions.py → 
   - 调用 SessionService.add_message() 保存用户消息
   - 调用 ai_service.generate_response() 生成 AI 响应
   - 再次调用 add_message() 保存 AI 响应
3. 返回 {response, session}
```

---

## 架构设计原则

### 1. 分层架构
```
API Layer (api/)
    ↓ 调用
Service Layer (services/)
    ↓ 调用
Data Layer (models/)
    ↓ 使用
Cache Layer (redis_client/)
```

### 2. 依赖注入
- 数据库会话通过 `Depends(get_db)` 注入
- 服务类通过构造函数注入依赖
- 便于单元测试和 Mock

### 3. 单例模式
- `redis_client`：全局 Redis 连接
- `ai_service`：全局 AI 服务实例
- `settings`：全局配置

### 4. 缓存策略
- **写入后失效**：修改数据后删除缓存
- **读取时加载**：缓存未命中时从数据库加载
- **TTL 过期**：设置缓存过期时间

---

## 扩展建议

### 添加新功能

1. **新 API 端点**：
   - 在 `api/v1/endpoints/` 创建新文件
   - 在 `api/v1/router.py` 注册路由

2. **新数据模型**：
   - 在 `models/` 创建模型类
   - 继承 `Base` 类
   - 运行应用自动创建表

3. **新业务逻辑**：
   - 在 `services/` 创建服务类
   - 通过构造函数注入依赖

4. **新异步任务**：
   - 在 `tasks/` 添加任务函数
   - 使用 `@celery_app.task` 装饰器

---

## 总结

`app` 目录采用清晰的分层架构：

- **api/**：处理 HTTP 请求和响应
- **core/**：提供通用功能（异常、中间件）
- **models/**：定义数据结构（数据库表）
- **schemas/**：定义数据验证规则
- **services/**：实现业务逻辑
- **tasks/**：处理异步任务
- **utils/**：提供工具函数

这种结构使得代码：
- ✅ 易于理解和维护
- ✅ 便于测试（各层可独立测试）
- ✅ 支持扩展（添加新功能不影响现有代码）
- ✅ 符合 FastAPI 最佳实践

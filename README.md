# 企业智能搜索系统

基于 DeepSeek ReAct Agent 的企业级智能搜索系统，具备多轮推理决策能力，可自主选择搜索策略，跨多个本地数据源迭代查询，最终汇总答案。

## 架构概述

```
用户提问 → DeepSeek 模型推理 → 选择搜索工具 → 获取结果 → 再次推理 → 继续搜索或输出答案
                                  ↑ 循环直到信息足够 ↑
```

系统维护了 9 类可搜索的数据源：

| 类型 | 数据源 | 底层技术 |
|------|--------|----------|
| 结构化数据 | 员工、部门、项目、客户、产品、订单、文档 | SQLite + SQLAlchemy |
| 语义搜索 | 文档内容的概念性匹配 | ChromaDB + text2vec |
| 关键词搜索 | 文档、日志的精确匹配（支持中文分词） | Whoosh + jieba |
| 系统日志 | 运行日志（按级别/时间过滤） | SQLite + Whoosh |
| 代码仓库 | 本地 Git 仓库代码符号搜索 | git grep |
| HR 系统 | 员工信息、组织架构、下属查询 | 模拟企业 SDK |
| CRM 系统 | 客户、订单、产品管理 | 模拟企业 SDK |
| 文档管理 | 政策、手册、报告、规范检索 | 模拟企业 SDK |
| 项目管理 | 项目进度、任务分配、工作负载 | 模拟企业 SDK |

## 项目结构

```
zhihu/
├── src/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 全局配置 (Settings)
│   ├── agent/                   # Agent 决策层
│   │   ├── agent_loop.py        # 多轮推理循环
│   │   ├── tool_definitions.py  # LLM 工具定义 + 系统提示词
│   │   ├── tool_registry.py     # 工具注册与执行
│   │   └── tracer.py            # 搜索步骤追踪
│   ├── api/                     # API 层
│   │   ├── router.py            # SSE 对话 + 直接搜索 + 统计
│   │   └── schemas.py           # Pydantic 模型
│   ├── search_engines/          # 搜索引擎
│   │   ├── base.py              # 基类 SearchEngine + SearchResult
│   │   ├── relational.py        # SQLite 关系型搜索
│   │   ├── vector_store.py      # ChromaDB 向量搜索
│   │   ├── keyword_search.py    # Whoosh 关键词搜索
│   │   ├── log_search.py        # 日志搜索
│   │   └── code_search.py       # 代码仓库搜索
│   ├── enterprise_systems/      # 模拟企业系统 SDK
│   │   ├── hr_system.py         # HR 系统
│   │   ├── crm_system.py        # CRM 系统
│   │   ├── doc_mgmt_system.py   # 文档管理系统
│   │   └── pm_system.py         # 项目管理系统
│   ├── models/                  # SQLAlchemy 数据模型
│   │   ├── base.py              # Base + TimestampMixin
│   │   ├── employee.py          # Employee, Department
│   │   ├── customer.py          # Customer, Product, Order, OrderItem
│   │   ├── project.py           # Project, Task
│   │   ├── document.py          # Document
│   │   └── log_entry.py         # LogEntry
│   ├── database/                # 数据库
│   │   ├── session.py           # 连接管理
│   │   └── seed.py              # 种子数据生成
│   ├── embeddings/              # 嵌入模型
│   │   └── embedder.py          # 文本向量化
│   ├── repo_manager/            # 代码仓库管理
│   │   └── git_manager.py       # Git 操作
│   ├── web_ui/                  # Web 前端
│   │   ├── views.py             # 页面路由
│   │   └── static/
│   │       ├── index.html       # 主页面
│   │       ├── app.js           # 主页面逻辑
│   │       ├── styles.css       # 样式
│   │       └── tracker.js       # 埋点 SDK
│   ├── admin/                   # 数据库管理后台
│   │   ├── views.py             # 页面路由
│   │   ├── router.py            # CRUD API
│   │   └── static/admin.html    # 管理界面
│   └── tracking/                # 埋点系统
│       ├── model.py             # 埋点数据模型
│       ├── router.py            # 埋点 API + 管理 API
│       └── static/tracking_admin.html  # 埋点管理界面
├── scripts/
│   ├── seed_all.py              # 一键初始化所有数据
│   └── build_mock_repos.py      # 构建模拟代码仓库
├── tests/
│   ├── conftest.py              # 测试配置
│   └── test_all.py              # 全量测试 (100+ 用例)
├── data/                        # 数据目录 (自动生成)
│   ├── sqlite/enterprise.db     # SQLite 数据库
│   ├── chroma/                  # ChromaDB 向量库
│   ├── whoosh_index/            # Whoosh 全文索引
│   ├── mock_repos/              # 模拟 Git 仓库
│   └── logs/app.log             # 应用日志
├── requirements.txt
├── .env                         # 环境变量配置
├── 测试计划.md                   # 详细测试计划
├── tracking_schema.json         # 埋点数据结构说明
└── tracking_payload_sample.json # 埋点请求示例
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Git（用于构建模拟代码仓库）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=your-api-key-here     # 必填：DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 4. 初始化数据

```bash
# 构建模拟 Git 代码仓库（2个仓库，含 Python 源码）
python scripts/build_mock_repos.py

# 初始化数据库 + 向量库 + 关键词索引
python scripts/seed_all.py
```

种子数据规模：

| 数据 | 数量 |
|------|------|
| 部门 | 5 |
| 员工 | 50 |
| 项目 | 8 |
| 任务 | 40 |
| 客户 | 30 |
| 产品 | 20 |
| 订单 | 60 |
| 文档 | 25 |
| 日志 | 500 |
| 代码仓库 | 2 |

### 5. 启动服务

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. 访问页面

| 地址 | 功能 |
|------|------|
| http://localhost:8000 | 智能搜索主页 |
| http://localhost:8000/admin | 数据库管理后台（CRUD） |
| http://localhost:8000/admin/tracking | 埋点数据管理 |

## API 接口

### 对话搜索

```
POST /api/chat
Content-Type: application/json
Response: text/event-stream (SSE)

{
  "query": "张鹏是哪个部门的？",
  "conversation_id": "可选，留空自动创建"
}
```

SSE 事件类型：`conversation_id` → `tool_call` → `tool_result` → `final_answer` → `done`

### 直接搜索（绕过 Agent）

```
POST /api/search/direct
{
  "query": "关键词",
  "engine": "relational | vector | keyword | log | code",
  "top_k": 10
}
```

### 系统统计

```
GET /api/stats
```

### 数据库管理

```
GET    /admin/api/tables              # 列出所有表
GET    /admin/api/tables/{name}/schema # 表结构
GET    /admin/api/tables/{name}/rows   # 分页查询
POST   /admin/api/tables/{name}/rows   # 新增行
PUT    /admin/api/tables/{name}/rows   # 更新行
PUT    /admin/api/tables/{name}/rows/soft-delete  # 软删除（停用）
PUT    /admin/api/tables/{name}/rows/soft-enable  # 启用
GET    /admin/api/tables/{name}/max-id # 获取最大 ID
```

### 埋点上报

```
GET /api/tracking/event?d=<base64url>    # 上报事件
GET /api/tracking/session?d=<base64url>  # 会话管理
GET /api/tracking/stats?days_back=7      # 统计汇总
GET /api/tracking/admin/events           # 管理：事件列表
GET /api/tracking/admin/event/{id}       # 管理：事件详情
GET /api/tracking/admin/sessions         # 管理：会话列表
```

## 埋点系统

前端 SDK（`tracker.js`）自动采集以下行为：

| trackName | 触发时机 | 关键数据 |
|-----------|----------|----------|
| `page_view` | 页面加载 | 性能指标 (DNS/TCP/TTFB/FCP)、浏览器信息、屏幕分辨率 |
| `click` | 元素点击 | 元素标签/ID/类名/CSS选择器、鼠标坐标、修饰键 |
| `scroll` | 滚动到里程碑 | 滚动深度 % (25/50/75/100)、文档高度 |
| `visibility` | 切换标签页 | 可见/隐藏状态、可见持续时长 |
| `error` | JS 异常 | 错误消息、堆栈、文件名、行号 |

特点：
- 浏览器指纹：Canvas + WebGL + Audio 多维度 → SHA-256，localStorage 持久化
- 数据编码：URL-safe Base64，GET 请求发送
- 事件即发：发生即发送，无批量积攒
- 手动埋点：`window.__tracker.track('custom', { label: 'xxx', payload: {...} })`

## 数据库管理后台

`/admin` 提供完整的数据库管理功能：

- 浏览所有 12 张表（含行数统计）
- 查看表结构（字段类型、主键、外键、自增）
- 分页浏览数据、搜索过滤、列排序
- 新增行（自增 ID 自动 max+1 预填）
- 编辑行（主键只读保护）
- 软删除/启用（检测 status/is_deleted/deleted_at 列自动适配）

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + SSE |
| 大模型 | DeepSeek (via OpenAI SDK) |
| 关系型数据库 | SQLite + SQLAlchemy 2.0 |
| 向量数据库 | ChromaDB |
| 全文搜索 | Whoosh + jieba 分词 |
| 嵌入模型 | shibing624/text2vec-base-chinese (确定性哈希) |
| 代码搜索 | git grep |
| 埋点 | 浏览器指纹 + sendBeacon/GET |
| 测试 | pytest + pytest-asyncio |

## 运行测试

```bash
# 运行全部测试 (100+ 用例)
pytest tests/ -v

# 按模块运行
pytest tests/test_all.py::TestRelationalDB -v
pytest tests/test_all.py::TestPerformance -v
```

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DEEPSEEK_API_KEY | - | DeepSeek API 密钥（必填） |
| DEEPSEEK_BASE_URL | https://api.deepseek.com | API 地址 |
| DEEPSEEK_MODEL | deepseek-chat | 模型名称 |
| EMBEDDING_DIMENSION | 768 | 嵌入向量维度 |
| AGENT_MAX_ITERATIONS | 10 | Agent 最大搜索轮次 |
| AGENT_TIMEOUT_SECONDS | 120 | 单次对话超时 |

## License

MIT

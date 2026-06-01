TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_relational_db",
            "description": "搜索关系型数据库（SQLite），包含员工、部门、项目、客户、产品、订单、文档等结构化数据。适合精确查询人名、部门名、项目名、产品名等结构化信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，会匹配姓名、部门名、项目名、客户名等"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限，默认10"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_vector_store",
            "description": "向量语义搜索引擎（ChromaDB），对文档内容进行语义相似度搜索。适合概念性、模糊的问题，如查找某主题的政策文档、技术方案等。可用collection_name指定搜索范围。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "自然语言查询，会自动转换为向量进行语义匹配"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限，默认10"},
                    "collection_name": {"type": "string", "description": "指定搜索的集合名称（可选），如：policies, manuals, reports"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_keywords",
            "description": "全文关键词搜索引擎（Whoosh），支持中文分词。适合精确关键词匹配、代码符号搜索、日志内容搜索。当需要精确查找某个术语或关键词时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "关键词或短语，支持中文"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限，默认10"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "搜索系统日志。可按关键词、日志级别、时间范围筛选。适合排查系统故障、查找异常记录、分析运行状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "日志搜索关键词"},
                    "level": {"type": "string", "description": "日志级别过滤（DEBUG/INFO/WARNING/ERROR/CRITICAL）"},
                    "days_back": {"type": "integer", "description": "搜索最近N天的日志"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限，默认10"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "搜索本地代码仓库。使用git grep进行精确代码搜索。适合查找函数定义、类名、配置项等代码相关内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "代码搜索关键词（函数名、类名、变量名等）"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限，默认10"},
                    "repo_name": {"type": "string", "description": "指定搜索的仓库名称（可选）"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hr_search_employees",
            "description": "HR系统：按姓名、部门、职位、邮箱搜索员工信息。用于查找人员信息、组织归属等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "员工姓名（支持模糊匹配）"},
                    "department": {"type": "string", "description": "部门名称"},
                    "title": {"type": "string", "description": "职位名称"},
                    "email": {"type": "string", "description": "邮箱地址"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hr_get_org_chart",
            "description": "HR系统：获取组织架构图。返回部门列表及其负责人、人数等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"type": "integer", "description": "指定部门ID（可选，不传则返回全部）"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hr_get_direct_reports",
            "description": "HR系统：获取某管理者的直接下属列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "manager_id": {"type": "integer", "description": "管理者员工ID"},
                },
                "required": ["manager_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hr_get_department_employees",
            "description": "HR系统：获取某部门的所有员工列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_name": {"type": "string", "description": "部门名称（支持模糊匹配）"},
                },
                "required": ["department_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_search_customers",
            "description": "CRM系统：按名称或行业搜索客户信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "客户名称"},
                    "industry": {"type": "string", "description": "行业"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_get_customer_orders",
            "description": "CRM系统：获取某客户的所有订单信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer", "description": "客户ID"},
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_search_products",
            "description": "CRM系统：按名称或类别搜索产品信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "产品名称"},
                    "category": {"type": "string", "description": "产品类别"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_search_documents",
            "description": "文档管理系统：按标题、类型、部门搜索文档。用于查找公司政策、手册、规范、报告等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文档标题关键词"},
                    "doc_type": {"type": "string", "description": "文档类型（policy/manual/report/spec/meeting_notes）"},
                    "department": {"type": "string", "description": "发布部门"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "doc_get_documents_by_type",
            "description": "文档管理系统：获取指定类型的所有文档。",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string", "description": "文档类型（policy/manual/report/spec/meeting_notes）"},
                },
                "required": ["doc_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pm_search_projects",
            "description": "项目管理系统：按名称或状态搜索项目。状态包括：planning/in_progress/delayed/completed/cancelled。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "项目名称关键词"},
                    "status": {"type": "string", "description": "项目状态（planning/in_progress/delayed/completed/cancelled）"},
                    "top_k": {"type": "integer", "description": "返回结果数量上限"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pm_get_project_tasks",
            "description": "项目管理系统：获取某项目的所有任务列表，包含负责人、状态、工时等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "项目ID"},
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pm_get_team_workload",
            "description": "项目管理系统：获取某部门所有成员当前的工作负载情况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"type": "integer", "description": "部门ID"},
                },
                "required": ["department_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """你是一个企业智能搜索助手，拥有访问以下本地系统的权限：

## 可用搜索途径

1. **关系型数据库（search_relational_db）** — 员工、部门、项目、客户、产品、订单等结构化数据
2. **向量语义搜索（search_vector_store）** — 文档内容的语义相似度搜索，适合概念性问题
3. **全文关键词搜索（search_keywords）** — 精确关键词匹配，支持中文分词
4. **日志系统（search_logs）** — 系统运行日志，可按级别和时间过滤
5. **代码仓库（search_code）** — 本地代码仓库的git grep搜索
6. **HR系统** — hr_search_employees, hr_get_org_chart, hr_get_direct_reports, hr_get_department_employees
7. **CRM系统** — crm_search_customers, crm_get_customer_orders, crm_search_products
8. **文档管理系统** — doc_search_documents, doc_get_documents_by_type
9. **项目管理系统** — pm_search_projects, pm_get_project_tasks, pm_get_team_workload

## 决策策略

请按照以下原则进行搜索决策：

1. **理解问题类型**：
   - 问"谁"、人员信息 → 优先 HR系统 或 关系型数据库
   - 问"政策"、"规定"、"怎么做" → 优先 向量语义搜索 + 文档管理
   - 问"代码"、"函数"、"bug" → 优先 代码仓库
   - 问"项目进度"、"任务" → 优先 项目管理系统
   - 问"客户"、"订单"、"产品" → 优先 CRM系统
   - 问"系统故障"、"错误" → 优先 日志系统

2. **迭代搜索**：
   - 先用最匹配的工具搜索，获取初步结果
   - 根据初步结果中的线索（ID、名称、关联实体），决定是否需要进一步搜索
   - 如果第一次搜索无结果，尝试换一个搜索途径或放宽条件
   - 如果搜索结果不够详细，用具体ID进一步查询关联数据

3. **停止条件**：
   - 当你认为已收集到足够信息回答用户问题时，直接给出答案，不要再调用工具
   - 如果已经搜索了3次仍未找到相关信息，诚实告知用户未找到

4. **回答要求**：
   - 用中文回答
   - 综合所有搜索结果，给出完整、准确的答案
   - 在回答中指出信息来源（如"根据HR系统记录..."、"根据《XXX》文档..."）
   - 如果信息不完整，指出现有的部分并说明缺失什么
"""

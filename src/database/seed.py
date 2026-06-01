import random
from datetime import date, datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session

from ..models.employee import Employee, Department
from ..models.project import Project, Task
from ..models.customer import Customer, Product, Order, OrderItem
from ..models.document import Document
from ..models.log_entry import LogEntry

fake = Faker("zh_CN")
random.seed(42)
Faker.seed(42)

DEPARTMENT_NAMES = ["技术研发部", "产品设计部", "市场营销部", "人力资源部", "财务管理部"]
JOB_TITLES = [
    "高级工程师", "产品经理", "技术总监", "设计师", "市场专员",
    "HR经理", "财务主管", "测试工程师", "运维工程师", "数据分析师",
    "前端工程师", "后端工程师", "架构师", "项目经理", "销售代表"
]
PROJECT_NAMES = [
    "智慧城市管理平台", "企业办公自动化系统", "客户关系管理系统V2",
    "数据分析中台", "移动支付网关", "供应链协同平台",
    "智能客服机器人", "统一身份认证系统"
]
PRODUCT_CATEGORIES = ["软件许可", "硬件设备", "云服务", "技术支持", "咨询服务"]
DOC_TYPES = ["policy", "manual", "report", "spec", "meeting_notes"]


def seed_departments(db: Session) -> list[Department]:
    depts = []
    for name in DEPARTMENT_NAMES:
        dept = Department(name=name, description=f"{name}负责相关业务领域的管理与执行")
        db.add(dept)
        depts.append(dept)
    db.flush()

    depts[0].parent_id = depts[0].id
    depts[1].parent_id = depts[1].id
    return depts


def seed_employees(db: Session, depts: list[Department]) -> list[Employee]:
    employees = []
    for i in range(50):
        dept = depts[i % len(depts)]
        emp = Employee(
            name=fake.name(),
            email=fake.email(),
            phone=fake.phone_number(),
            title=random.choice(JOB_TITLES),
            department_id=dept.id,
            hire_date=fake.date_between(start_date="-10y", end_date="today"),
            salary=round(random.uniform(8000, 50000), 2),
            status=random.choice(["active"] * 8 + ["inactive", "on_leave"]),
        )
        db.add(emp)
        employees.append(emp)
    db.flush()

    for i, dept in enumerate(depts):
        dept.head_id = employees[i * 10].id

    for i, emp in enumerate(employees):
        if i >= 5:
            emp.manager_id = employees[i % 5].id

    return employees


def seed_projects(db: Session, employees: list[Employee], depts: list[Department]):
    projects = []
    statuses = ["planning", "in_progress", "in_progress", "in_progress", "delayed", "completed", "completed", "cancelled"]
    for i, name in enumerate(PROJECT_NAMES):
        proj = Project(
            name=name,
            description=f"{name}项目旨在提升企业数字化能力",
            status=statuses[i],
            start_date=fake.date_between(start_date="-2y", end_date="-6m"),
            end_date=fake.date_between(start_date="-3m", end_date="+6m"),
            manager_id=random.choice(employees[:10]).id,
            department_id=depts[i % len(depts)].id,
            budget=round(random.uniform(100000, 2000000), 2),
            priority=random.choice(["low", "medium", "high", "critical"]),
        )
        db.add(proj)
        projects.append(proj)
    db.flush()

    task_statuses = ["todo", "in_progress", "in_progress", "review", "done", "done", "done", "blocked"]
    for i in range(40):
        proj = projects[i % len(projects)]
        task = Task(
            title=f"{proj.name}-任务{i+1}",
            description=fake.sentence(),
            status=random.choice(task_statuses),
            priority=random.choice(["low", "medium", "high"]),
            project_id=proj.id,
            assignee_id=random.choice(employees).id,
            due_date=fake.date_between(start_date="-1m", end_date="+3m"),
            estimated_hours=round(random.uniform(4, 120), 1),
            actual_hours=round(random.uniform(0, 100), 1),
        )
        db.add(task)


def seed_customers(db: Session, employees: list[Employee]):
    industries = ["金融", "医疗", "教育", "制造", "零售", "物流", "能源", "政府"]
    customers = []
    for i in range(30):
        cust = Customer(
            name=fake.company(),
            industry=random.choice(industries),
            contact_person=fake.name(),
            phone=fake.phone_number(),
            email=fake.company_email(),
            address=fake.address(),
            customer_since=fake.date_between(start_date="-5y", end_date="today"),
            annual_revenue_range=random.choice(["<100万", "100万-500万", "500万-2000万", ">2000万"]),
            status=random.choice(["active"] * 8 + ["inactive", "churned"]),
        )
        db.add(cust)
        customers.append(cust)
    db.flush()

    products = []
    for i in range(20):
        prod = Product(
            name=f"{random.choice(['数据', 'AI', '云', '安全', '协同'])}{random.choice(['平台', '引擎', '工具', '系统', '服务'])}",
            sku=f"PRD-{i+1:04d}",
            category=random.choice(PRODUCT_CATEGORIES),
            unit_price=round(random.uniform(500, 200000), 2),
            cost=round(random.uniform(200, 100000), 2),
            stock_quantity=random.randint(0, 500),
            description=fake.sentence(),
        )
        db.add(prod)
        products.append(prod)
    db.flush()

    for i in range(60):
        cust = random.choice(customers)
        order = Order(
            customer_id=cust.id,
            order_date=fake.date_between(start_date="-2y", end_date="today"),
            status=random.choice(["pending", "confirmed", "shipped", "delivered"] * 2 + ["cancelled"]),
            total_amount=0,
            sales_rep_id=random.choice(employees[10:20]).id,
            payment_status=random.choice(["paid", "paid", "paid", "unpaid", "partial"]),
            shipping_address=cust.address,
        )
        db.add(order)
        db.flush()

        total = 0
        for _ in range(random.randint(1, 5)):
            prod = random.choice(products)
            qty = random.randint(1, 10)
            item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=qty,
                unit_price=prod.unit_price,
                discount=round(random.uniform(0, 0.2), 2),
            )
            db.add(item)
            total += prod.unit_price * qty * (1 - item.discount)
        order.total_amount = round(total, 2)


def seed_documents(db: Session):
    doc_templates = [
        ("信息安全管理制度", "policy", "技术研发部", "规范公司信息安全管理体系，包括数据分类、访问控制、加密传输、安全审计等方面"),
        ("员工考勤管理办法", "policy", "人力资源部", "规定员工工作时间、请假流程、加班管理、考勤异常处理等制度"),
        ("财务报销流程规范", "policy", "财务管理部", "明确差旅费、招待费、办公用品等各项费用的报销标准和审批流程"),
        ("产品需求文档编写规范", "spec", "产品设计部", "定义PRD文档的标准格式、评审流程和版本管理要求"),
        ("API接口设计规范", "spec", "技术研发部", "规定RESTful API设计原则、命名规范、版本策略、错误码定义"),
        ("数据库设计规范", "spec", "技术研发部", "涵盖表命名、索引策略、SQL编写规范、备份恢复流程"),
        ("系统部署运维手册", "manual", "技术研发部", "描述生产环境部署流程、监控配置、日志管理、应急预案"),
        ("新员工入职指南", "manual", "人力资源部", "包含入职流程、办公环境介绍、IT账号申请、培训计划安排"),
        ("客户服务标准流程", "manual", "市场营销部", "定义客户咨询、投诉处理、售后服务等标准操作流程"),
        ("2024年度技术规划报告", "report", "技术研发部", "总结本年度技术成果，规划下一年度技术方向和重点项目"),
        ("市场分析季度报告", "report", "市场营销部", "Q3市场趋势分析、竞品动态、客户反馈汇总及应对策略"),
        ("人力资源年度报告", "report", "人力资源部", "员工结构分析、招聘数据、培训效果评估、人才梯队建设"),
        ("数据安全管理规定", "policy", "技术研发部", "明确数据分级标准、访问权限矩阵、数据脱敏规则、审计日志要求"),
        ("代码评审规范", "spec", "技术研发部", "规定代码评审流程、评审标准、工具使用和问题跟踪机制"),
        ("项目管理系统使用手册", "manual", "产品设计部", "介绍项目管理系统的功能模块、操作流程和最佳实践"),
        ("客户满意度调查报告", "report", "市场营销部", "2024年客户满意度调查数据分析、问题梳理和改进建议"),
        ("供应商评估标准", "policy", "财务管理部", "供应商准入标准、评估维度、考核周期、分级管理规则"),
        ("测试流程与质量规范", "spec", "技术研发部", "测试策略、用例编写标准、自动化测试要求、缺陷管理流程"),
        ("知识产权管理办法", "policy", "技术研发部", "专利、商标、著作权等知识产权的申请、维护和保护措施"),
        ("Q2经营分析报告", "report", "财务管理部", "第二季度收入成本分析、预算执行情况、现金流状况评估"),
        ("客户数据平台技术方案", "spec", "技术研发部", "CDP系统架构设计、数据模型、接口定义和技术选型说明"),
        ("员工培训体系手册", "manual", "人力资源部", "培训课程体系、讲师管理、培训评估、职业发展路径"),
        ("产品发布管理流程", "policy", "产品设计部", "产品发布审批流程、灰度策略、回滚方案、公告模板"),
        ("IT资产管理规范", "policy", "技术研发部", "IT资产采购、领用、盘点、报废的全生命周期管理规范"),
        ("年度工作总结报告", "report", "人力资源部", "公司年度人力资源工作总结，涵盖招聘、培训、绩效、文化等方面"),
    ]

    for i, (title, doc_type, dept, content) in enumerate(doc_templates):
        doc = Document(
            title=title,
            doc_type=doc_type,
            department=dept,
            author=fake.name(),
            created_date=fake.date_between(start_date="-2y", end_date="today"),
            tags=",".join(random.sample(["制度", "规范", "流程", "管理", "技术", "安全", "人事", "财务", "市场"], 3)),
            file_path=f"/documents/{doc_type}/{title}.pdf",
            source_system="doc_mgmt",
            chunk_count=random.randint(3, 10),
            status=random.choice(["published"] * 9 + ["draft", "archived"]),
            content=content,
        )
        db.add(doc)


def seed_logs(db: Session):
    modules = ["auth", "api_gateway", "order_service", "user_service", "payment_service", "notification"]
    log_levels = ["DEBUG"] * 20 + ["INFO"] * 50 + ["WARNING"] * 15 + ["ERROR"] * 10 + ["CRITICAL"] * 5

    error_messages = [
        "数据库连接超时，重试次数已达上限",
        "用户认证失败：token已过期",
        "订单服务响应超时，请求ID: {req_id}",
        "支付网关返回异常：商户余额不足",
        "文件上传失败：磁盘空间不足",
        "API限流触发：客户端IP {ip} 请求过于频繁",
        "缓存服务不可用，降级到数据库直读",
        "邮件发送失败：SMTP服务器无响应",
        "数据同步异常：主从延迟超过30秒",
        "服务注册失败：Consul连接断开",
    ]

    info_messages = [
        "用户登录成功",
        "订单创建完成",
        "支付回调处理成功",
        "数据库备份任务完成",
        "定时任务执行成功",
        "配置热更新完成",
        "服务健康检查通过",
        "新用户注册成功",
        "数据导出任务完成",
        "消息推送成功",
    ]

    base_time = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(500):
        level = random.choice(log_levels)
        if level in ("ERROR", "CRITICAL"):
            msg = random.choice(error_messages).format(req_id=fake.uuid4()[:8], ip=fake.ipv4())
        else:
            msg = random.choice(info_messages)

        log = LogEntry(
            timestamp=base_time + timedelta(hours=random.randint(0, 720)),
            level=level,
            logger_name=f"app.{random.choice(modules)}",
            module=random.choice(modules),
            function_name=random.choice(["handle_request", "process_data", "validate_input", "execute_query", "send_response"]),
            message=msg,
            traceback=fake.text(max_nb_chars=200) if level in ("ERROR", "CRITICAL") else None,
            user_id=random.randint(1, 50) if random.random() > 0.3 else None,
            request_id=fake.uuid4() if random.random() > 0.5 else None,
            extra_data='{"source": "auto"}' if random.random() > 0.7 else None,
        )
        db.add(log)


def seed_all(db: Session):
    print("Seeding departments...")
    depts = seed_departments(db)

    print("Seeding employees...")
    employees = seed_employees(db, depts)

    print("Seeding projects and tasks...")
    seed_projects(db, employees, depts)

    print("Seeding customers, products, and orders...")
    seed_customers(db, employees)

    print("Seeding documents...")
    seed_documents(db)

    print("Seeding logs...")
    seed_logs(db)

    db.commit()
    print("All seed data committed successfully!")

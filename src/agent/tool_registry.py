import json
from typing import Any
from ..search_engines.relational import relational_engine
from ..search_engines.vector_store import vector_engine
from ..search_engines.keyword_search import keyword_engine
from ..search_engines.log_search import log_engine
from ..search_engines.code_search import code_engine
from ..enterprise_systems.hr_system import hr_system
from ..enterprise_systems.crm_system import crm_system
from ..enterprise_systems.doc_mgmt_system import doc_mgmt_system
from ..enterprise_systems.pm_system import pm_system


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, callable] = {}

    def register(self, name: str, func: callable):
        self._tools[name] = func

    async def execute(self, tool_name: str, **kwargs) -> list[dict]:
        func = self._tools.get(tool_name)
        if not func:
            return [{"error": f"Unknown tool: {tool_name}"}]
        try:
            result = func(**kwargs)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                return [{"result": str(result)}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())


tool_registry = ToolRegistry()


def _wrap_search(func):
    def wrapper(query: str, top_k: int = 10, **kwargs):
        results = func(query, top_k=top_k, **kwargs)
        return [r.to_dict() for r in results]
    return wrapper


tool_registry.register("search_relational_db", _wrap_search(relational_engine.search))
tool_registry.register("search_vector_store", _wrap_search(vector_engine.search))
tool_registry.register("search_keywords", _wrap_search(keyword_engine.search))
tool_registry.register("search_logs", _wrap_search(log_engine.search))
tool_registry.register("search_code", _wrap_search(code_engine.search))

tool_registry.register("hr_search_employees", hr_system.search_employees)
tool_registry.register("hr_get_org_chart", hr_system.get_org_chart)
tool_registry.register("hr_get_direct_reports", hr_system.get_direct_reports)
tool_registry.register("hr_get_department_employees", hr_system.get_department_employees)

tool_registry.register("crm_search_customers", crm_system.search_customers)
tool_registry.register("crm_get_customer_orders", crm_system.get_customer_orders)
tool_registry.register("crm_search_products", crm_system.search_products)

tool_registry.register("doc_search_documents", doc_mgmt_system.search_documents)
tool_registry.register("doc_get_documents_by_type", doc_mgmt_system.get_documents_by_type)

tool_registry.register("pm_search_projects", pm_system.search_projects)
tool_registry.register("pm_get_project_tasks", pm_system.get_project_tasks)
tool_registry.register("pm_get_team_workload", pm_system.get_team_workload)

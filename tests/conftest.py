import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.session import SessionLocal
from src.search_engines.relational import relational_engine
from src.search_engines.vector_store import vector_engine
from src.search_engines.keyword_search import keyword_engine
from src.search_engines.log_search import log_engine
from src.search_engines.code_search import code_engine
from src.enterprise_systems.hr_system import hr_system
from src.enterprise_systems.crm_system import crm_system
from src.enterprise_systems.doc_mgmt_system import doc_mgmt_system
from src.enterprise_systems.pm_system import pm_system
from src.agent.tool_registry import tool_registry
from src.agent.tracer import tracer, TraceStep
from src.repo_manager.git_manager import git_manager


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

from pydantic_settings import BaseSettings


import os as _os

_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_DB_PATH = _BASE_DIR.replace("\\", "/") + "/data/sqlite/enterprise.db"


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    embedding_model: str = "shibing624/text2vec-base-chinese"
    embedding_dimension: int = 768

    sqlite_url: str = f"sqlite:///{_DB_PATH}"
    chroma_persist_dir: str = _os.path.join(_BASE_DIR, "data", "chroma")
    whoosh_index_dir: str = _os.path.join(_BASE_DIR, "data", "whoosh_index")
    mock_repos_dir: str = _os.path.join(_BASE_DIR, "data", "mock_repos")
    log_file: str = _os.path.join(_BASE_DIR, "data", "logs", "app.log")

    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

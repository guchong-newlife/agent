import os
from ..config import settings


class GitManager:
    def __init__(self):
        self.repos_dir = os.path.abspath(settings.mock_repos_dir)
        os.makedirs(self.repos_dir, exist_ok=True)

    def list_repos(self) -> list[str]:
        repos = []
        if not os.path.isdir(self.repos_dir):
            return repos
        for name in os.listdir(self.repos_dir):
            path = os.path.join(self.repos_dir, name)
            if os.path.isdir(os.path.join(path, ".git")):
                repos.append(name)
        return repos

    def get_repo_path(self, name: str) -> str:
        return os.path.join(self.repos_dir, name)

    def grep_code(self, pattern: str, repo_name: str | None = None) -> list[dict]:
        import subprocess
        results = []
        repos = [repo_name] if repo_name else self.list_repos()

        for repo in repos:
            repo_path = self.get_repo_path(repo)
            try:
                output = subprocess.check_output(
                    ["git", "grep", "-n", "-i", pattern],
                    cwd=repo_path,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=10,
                )
                for line in output.strip().split("\n"):
                    if ":" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            results.append({
                                "repo": repo,
                                "file": parts[0],
                                "line": parts[1],
                                "content": parts[2].strip(),
                            })
            except subprocess.CalledProcessError:
                pass
            except Exception:
                pass

        return results

    def search_files(self, pattern: str, repo_name: str | None = None) -> list[dict]:
        import fnmatch
        results = []
        repos = [repo_name] if repo_name else self.list_repos()

        for repo in repos:
            repo_path = self.get_repo_path(repo)
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d != ".git"]
                for f in files:
                    if fnmatch.fnmatch(f, pattern):
                        results.append({
                            "repo": repo,
                            "file": os.path.relpath(os.path.join(root, f), repo_path),
                        })
        return results


git_manager = GitManager()

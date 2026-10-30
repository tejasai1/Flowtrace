import os
from dataclasses import dataclass
from pathlib import Path

# Folders that never contain useful source code.
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
             "dist", "build", ".idea", ".vscode", "output"}

CODE_EXTENSIONS = {".py": "python", ".js": "javascript", ".ts": "typescript",
                   ".java": "java", ".go": "go", ".rb": "ruby", ".php": "php",
                   ".cs": "csharp"}
CONFIG_EXTENSIONS = {".yaml": "yaml", ".yml": "yaml", ".json": "json",
                     ".toml": "toml", ".ini": "ini"}
CONFIG_NAMES = {"dockerfile": "dockerfile", ".env.example": "env",
                "requirements.txt": "requirements"}

MAX_FILE_SIZE = 100_000  # bytes; skip very large files


@dataclass
class SourceFile:
    repo: str       # repository name
    path: str       # path inside the repository
    kind: str       # "code", "config" or "schema"
    language: str
    content: str


def is_secret_file(name):
    """Real .env files hold secrets and must never be sent to a model."""
    name = name.lower()
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def classify(path):
    name = path.name.lower()
    if name in CONFIG_NAMES:
        return "config", CONFIG_NAMES[name]
    ext = path.suffix.lower()
    if ext in CODE_EXTENSIONS:
        return "code", CODE_EXTENSIONS[ext]
    if ext in CONFIG_EXTENSIONS:
        return "config", CONFIG_EXTENSIONS[ext]
    if ext == ".sql":
        return "schema", "sql"
    return None, None


def read_repository(repo_path, repo_name=None):
    """Collect the code, config and schema files of one repository."""
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Repository folder not found: {root}")
    name = repo_name or root.name
    files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Don't even enter skipped folders (much faster than filtering later).
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if is_secret_file(filename):
                continue
            kind, language = classify(path)
            if kind is None or path.stat().st_size > MAX_FILE_SIZE:
                continue
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue  # not a text file we can read
            files.append(SourceFile(name, path.relative_to(root).as_posix(),
                                    kind, language, content))
    return files
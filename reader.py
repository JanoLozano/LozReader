from pathlib import Path

from .adapters.python_adapter import PythonAdapter
from .models import ModuleModel

class Reader:
    def __init__(self):
        self.adapters = [
            PythonAdapter()
        ]

    def read(self, file_path: Path, relative_path: Path) -> ModuleModel | None:

        for adapter in self.adapters:
            if adapter.supports(file_path):
                return adapter.read(file_path, relative_path)
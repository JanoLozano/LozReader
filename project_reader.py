from pathlib import Path

from .models import ProjectModel, DirectoryModel, FileModel
from .reader import PythonAdapter


DEFAULT_IGNORED_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
}


class ProjectReader:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.python_reader = PythonAdapter()

    def read(self) -> ProjectModel:
        project_model = ProjectModel(
            name=self.project_path.name
        )

        # Estructura de carpetas y archivos
        project_model.root = self._read_directory(
            self.project_path
        )

        # Lectura de módulos Python
        for file_path in self.project_path.rglob("*.py"):

            if any(part in DEFAULT_IGNORED_DIRS for part in file_path.parts):
                continue

            relative_path = file_path.relative_to(
                self.project_path
            )

            module_model = self.python_reader.read(
                file_path,
                relative_path
            )

            project_model.modules.append(
                module_model
            )

        return project_model

    def _read_directory(
        self,
        directory_path: Path
    ) -> DirectoryModel:

        directory_model = DirectoryModel(
            name=directory_path.name
        )

        for item in directory_path.iterdir():

            # Carpeta
            if item.is_dir():

                if item.name in DEFAULT_IGNORED_DIRS:
                    continue

                child_directory = self._read_directory(
                    item
                )

                directory_model.directories.append(
                    child_directory
                )

            # Archivo
            elif item.is_file():

                file_model = FileModel(
                    name=item.name
                )

                directory_model.files.append(
                    file_model
                )

        return directory_model
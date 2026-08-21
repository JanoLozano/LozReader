from pathlib import Path

from .models import ProjectModel, DirectoryModel

class ReportGenerator:
    def generate(self, project: ProjectModel, output_dir: str = "report"):
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        tree_content = self._build_tree(project.root)

        tree_file = output_path / "tree.txt"

        tree_file.write_text(
            tree_content,
            encoding="utf-8"
        )

    def _build_tree(
        self,
        directory: DirectoryModel,
        prefix: str = ""
    ) -> str:

        lines = []

        lines.append(f"{prefix}{directory.name}/")

        entries = (
            directory.directories +
            directory.files
        )

        for index, entry in enumerate(entries):

            is_last = index == len(entries) - 1

            connector = "└── " if is_last else "├── "

            if isinstance(entry, DirectoryModel):

                child_prefix = (
                    prefix + "    "
                    if is_last
                    else prefix + "│   "
                )

                child_tree = self._build_tree(
                    entry,
                    child_prefix
                )

                child_lines = child_tree.splitlines()

                lines.append(
                    f"{prefix}{connector}{child_lines[0].strip()}"
                )

                lines.extend(
                    child_lines[1:]
                )

            else:
                lines.append(
                    f"{prefix}{connector}{entry.name}"
                )

        return "\n".join(lines)
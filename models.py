from dataclasses import dataclass, field

# Representa un import y el contexto en el que aparece.
@dataclass
class ImportModel:
    statement: str  # Import completo.
    kind: str  # Tipo de import: "import" o "from".
    scope: str  # Lugar donde se encuentra el import.
    owner: str | None = None  # Clase o función a la que pertenece.

# Representa un decorador aplicado a una función o método.
@dataclass
class DecoratorModel:
    statement: str
    name: str
    arguments: list[str] = field(default_factory=list)

# Representa un parámetro de una función o método.
@dataclass
class ParameterModel:
    name: str
    type_hint: str | None = None
    default: str | None = None

# Representa un atributo declarado en una clase.
@dataclass
class AttributeModel:
    name: str
    type_hint: str | None = None
    value: str | None = None

# Representa una función, incluyendo sus parámetros, retorno y decoradores.
@dataclass
class FunctionModel:
    name: str
    parameters: list[ParameterModel] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[DecoratorModel] = field(default_factory=list)

# Representa una clase y los elementos definidos dentro de ella.
@dataclass
class ClassModel:
    name: str
    bases: list[str] = field(default_factory=list)
    attributes: list[AttributeModel] = field(default_factory=list)
    methods: list[FunctionModel] = field(default_factory=list)
    imports: list[ImportModel] = field(default_factory=list)
    decorators: list[DecoratorModel] = field(default_factory=list)

# Representa un módulo Python y sus elementos de nivel superior.
@dataclass
class ModuleModel:
    path: str
    imports: list[ImportModel] = field(default_factory=list)
    classes: list[ClassModel] = field(default_factory=list)
    functions: list[FunctionModel] = field(default_factory=list)

# Representa un archivo dentro del árbol físico del proyecto.
@dataclass
class FileModel:
    name: str

# Representa un directorio y sus archivos y subdirectorios.
@dataclass
class DirectoryModel:
    name: str
    files: list[FileModel] = field(default_factory=list)
    directories: list["DirectoryModel"] = field(default_factory=list)

# Representa el proyecto completo: módulos analizados y su árbol de archivos.
@dataclass
class ProjectModel:
    name: str
    modules: list[ModuleModel] = field(default_factory=list)
    root: DirectoryModel | None = None
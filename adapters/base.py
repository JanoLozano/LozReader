from abc import ABC, abstractmethod
from pathlib import Path

from ..models import (
    ModuleModel,
    ClassModel,
    FunctionModel,
    AttributeModel,
    ImportModel,
)

class LanguageAdapter(ABC):

    @abstractmethod
    def read(
        self,
        file_path: Path,
        relative_path: Path
    ) -> ModuleModel:
        """
        Lee un archivo del lenguaje soportado
        y devuelve su representación LOZ.
        """
        pass

    @abstractmethod
    def _read_class(
        self,
        class_node,
        source
    ) -> ClassModel:
        """
        Lee una clase y la transforma en ClassModel.
        """
        pass

    @abstractmethod
    def _read_function(
        self,
        function_node,
        source
    ) -> FunctionModel:
        """
        Lee una función o método y la transforma
        en FunctionModel.
        """
        pass

    @abstractmethod
    def _read_import(
        self,
        import_node,
        source
    ) -> ImportModel:
        """
        Lee un import/dependencia del lenguaje
        y lo transforma en ImportModel.
        """
        pass

    @abstractmethod
    def _read_attribute(
        self,
        attribute_node,
        source
    ) -> AttributeModel | None:
        """
        Lee un atributo/variable declarada
        y la transforma en AttributeModel.
        """
        pass
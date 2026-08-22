from pathlib import Path

import libcst as cst

from .base import LanguageAdapter
from ..models import (
    ModuleModel,
    ImportModel,
    ClassModel,
    FunctionModel,
    AttributeModel,
    ParameterModel,
    DecoratorModel,
)


class PythonAdapter(LanguageAdapter):

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".py"

    def read(self, file_path: Path, relative_path: Path) -> ModuleModel:
        source = file_path.read_text(encoding="utf-8")
        module = cst.parse_module(source)

        module_model = ModuleModel(
            path=str(relative_path)
        )

        for statement in module.body:

            # Import / from import a nivel módulo
            if isinstance(statement, cst.SimpleStatementLine):
                imports = self._read_import(
                    statement,
                    scope="module",
                    owner=None
                )

                module_model.imports.extend(
                    imports
                )

            # Clase
            elif isinstance(statement, cst.ClassDef):
                class_model = self._read_class(
                    statement
                )

                module_model.classes.append(
                    class_model
                )

            # Función
            elif isinstance(statement, cst.FunctionDef):
                function_model, function_imports = self._read_function(
                    statement,
                    scope="function"
                )

                module_model.functions.append(
                    function_model
                )

                module_model.imports.extend(
                    function_imports
                )

        return module_model

    def _read_class(self, class_node: cst.ClassDef) -> ClassModel:
        class_model = ClassModel(
            name=class_node.name.value
        )

        # Herencia
        for base in class_node.bases:
            base_name = self._get_code(
                base.value
            )

            class_model.bases.append(
                base_name
            )

        # Decoradores
        for decorator in class_node.decorators:
            decorator_model = self._read_decorator(
                decorator
            )

            class_model.decorators.append(
                decorator_model
            )

        # Body de la clase
        if isinstance(class_node.body, cst.IndentedBlock):

            for statement in class_node.body.body:

                # Imports o atributos
                if isinstance(statement, cst.SimpleStatementLine):

                    imports = self._read_import(
                        statement,
                        scope="class",
                        owner=class_model.name
                    )

                    class_model.imports.extend(
                        imports
                    )

                    attribute_models = self._read_attribute(
                        statement
                    )

                    class_model.attributes.extend(
                        attribute_models
                    )

                # Método
                elif isinstance(statement, cst.FunctionDef):
                    method_model, method_imports = self._read_function(
                        statement,
                        scope="method"
                    )

                    class_model.methods.append(
                        method_model
                    )

                    class_model.imports.extend(
                        method_imports
                    )

        return class_model

    def _read_function(self, function_node: cst.FunctionDef, scope: str) -> tuple[FunctionModel, list[ImportModel]]:
        function_name = function_node.name.value

        function_model = FunctionModel(
            name=function_name
        )

        function_imports = []

        # Parámetros
        parameters = self._get_parameters(
            function_node.params
        )

        function_model.parameters.extend(
            parameters
        )

        # Tipo de retorno
        if function_node.returns is not None:
            function_model.return_type = self._get_code(
                function_node.returns.annotation
            )

        # Decoradores
        for decorator in function_node.decorators:
            decorator_model = self._read_decorator(
                decorator
            )

            function_model.decorators.append(
                decorator_model
            )

        # Body de función/método
        if isinstance(function_node.body, cst.IndentedBlock):

            for statement in function_node.body.body:

                if isinstance(statement, cst.SimpleStatementLine):
                    imports = self._read_import(
                        statement,
                        scope=scope,
                        owner=function_name
                    )

                    function_imports.extend(
                        imports
                    )

        return function_model, function_imports

    def _read_import(self, statement: cst.SimpleStatementLine, scope: str, owner: str | None) -> list[ImportModel]:
        imports = []

        for small_statement in statement.body:

            if isinstance(small_statement, cst.Import):
                import_model = ImportModel(
                    statement=self._get_code(small_statement),
                    kind="import",
                    scope=scope,
                    owner=owner
                )

                imports.append(
                    import_model
                )

            elif isinstance(small_statement, cst.ImportFrom):
                import_model = ImportModel(
                    statement=self._get_code(small_statement),
                    kind="from",
                    scope=scope,
                    owner=owner
                )

                imports.append(
                    import_model
                )

        return imports

    def _read_attribute(self, statement: cst.SimpleStatementLine) -> list[AttributeModel]:
        attributes = []

        for small_statement in statement.body:

            # atributo = valor
            if isinstance(small_statement, cst.Assign):

                if len(small_statement.targets) == 0:
                    continue

                target = small_statement.targets[0].target

                attribute_model = AttributeModel(
                    name=self._get_code(target),
                    value=self._get_code(small_statement.value)
                )

                attributes.append(
                    attribute_model
                )

            # atributo: tipo = valor
            elif isinstance(small_statement, cst.AnnAssign):

                attribute_name = self._get_code(
                    small_statement.target
                )

                type_hint = self._get_code(
                    small_statement.annotation.annotation
                )

                attribute_value = None

                if small_statement.value is not None:
                    attribute_value = self._get_code(
                        small_statement.value
                    )

                attribute_model = AttributeModel(
                    name=attribute_name,
                    type_hint=type_hint,
                    value=attribute_value
                )

                attributes.append(
                    attribute_model
                )

        return attributes

    def _get_parameters(self, parameters: cst.Parameters) -> list[ParameterModel]:
        parameter_models = []

        all_parameters = []

        all_parameters.extend(
            parameters.posonly_params
        )

        all_parameters.extend(
            parameters.params
        )

        if isinstance(parameters.star_arg, cst.Param):
            all_parameters.append(
                parameters.star_arg
            )

        all_parameters.extend(
            parameters.kwonly_params
        )

        if parameters.star_kwarg is not None:
            all_parameters.append(
                parameters.star_kwarg
            )

        for parameter in all_parameters:
            parameter_model = self._read_parameter(
                parameter
            )

            parameter_models.append(
                parameter_model
            )

        return parameter_models

    def _read_parameter(self, parameter: cst.Param) -> ParameterModel:
        parameter_name = parameter.name.value

        star = getattr(
            parameter,
            "star",
            ""
        )

        if star:
            parameter_name = f"{star}{parameter_name}"

        type_hint = None

        if parameter.annotation is not None:
            type_hint = self._get_code(
                parameter.annotation.annotation
            )

        default = None

        if parameter.default is not None:
            default = self._get_code(
                parameter.default
            )

        return ParameterModel(
            name=parameter_name,
            type_hint=type_hint,
            default=default
        )

    def _read_decorator(self, decorator: cst.Decorator) -> DecoratorModel:
        expression = decorator.decorator

        statement = f"@{self._get_code(expression)}"

        # @decorador(...)
        if isinstance(expression, cst.Call):
            decorator_name = self._get_code(
                expression.func
            )

            arguments = []

            for argument in expression.args:
                arguments.append(
                    self._get_code(argument)
                )

            return DecoratorModel(
                statement=statement,
                name=decorator_name,
                arguments=arguments
            )

        # @decorador
        decorator_name = self._get_code(
            expression
        )

        return DecoratorModel(
            statement=statement,
            name=decorator_name,
            arguments=[]
        )

    def _get_code(self, node: cst.CSTNode) -> str:
        return cst.Module([]).code_for_node(
            node
        ).strip()
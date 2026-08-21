from pathlib import Path
from platform import node

import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from .models import ImportModel, ModuleModel, ClassModel, ParameterModel
from .models import ModuleModel, ClassModel, AttributeModel, FunctionModel, DecoratorModel

PYTHON_LANGUAGE = Language(tspython.language())

class PythonReader:
    def __init__(self):
        self.parser = Parser(PYTHON_LANGUAGE)

    def read(self, file_path: Path, relative_path: Path) -> ModuleModel:
        source = file_path.read_bytes()
        tree = self.parser.parse(source)

        module_model = ModuleModel(
            path=str(relative_path)
        )

        for node in tree.root_node.children:

            if node.type == "import_statement":
                import_model = ImportModel(
                        statement=self._get_node_text(node, source),
                        kind="import",
                        scope="module"
                    )
                module_model.imports.append(import_model)
            elif node.type == "import_from_statement":
                import_model = ImportModel(
                    statement=self._get_node_text(node, source),
                    kind="from",
                    scope="module"
                )

                module_model.imports.append(import_model)
            elif node.type == "class_definition":
                class_model = self._read_class(
                    node,
                    source
                )
                module_model.classes.append(
                    class_model
                )
            elif node.type == "function_definition":
                function_model, function_imports = self._read_function(
                    node,
                    source
                    )

                module_model.functions.append(
                    function_model
                )

                module_model.imports.extend(
                    function_imports
                )
            elif node.type == "decorated_definition":
                definition_node = node.child_by_field_name("definition")

                if definition_node is not None and definition_node.type == "function_definition":
                    function_model, function_imports = self._read_function(
                        definition_node,
                        source
                    )

                    for child in node.named_children:
                        if child.type == "decorator":
                            decorator_text = self._get_node_text(
                                child,
                                source
                            )

                            function_model.decorators.append(
                                decorator_text
                            )

                    module_model.functions.append(
                        function_model
                    )

                    module_model.imports.extend(
                        function_imports
                    )
                elif (
                    definition_node is not None and definition_node.type == "class_definition"
                ):
                    if definition_node.type == "decorator":
                        decorator_model = self._read_decorators(
                            definition_node,
                            source
                        )

                        module_model.decorators.append(
                            decorator_model
                        )

        return module_model

    def _get_node_text(self,node,source: bytes) -> str:
        return source[
            node.start_byte:node.end_byte
        ].decode("utf-8")

    # extrae la información de una clase a partir del nodo del árbol de sintaxis
    def _read_class(self, class_node, source: bytes) -> ClassModel:

        # Nombre de la clase
        name_node = class_node.child_by_field_name("name")

        class_name = self._get_node_text(
            name_node,
            source
        )

        class_model = ClassModel(
            name=class_name
        )

        # Superclases / herencia
        superclasses_node = class_node.child_by_field_name(
            "superclasses"
        )

        if superclasses_node is not None:
            for child in superclasses_node.named_children:
                base_name = self._get_node_text(
                    child,
                    source
                )

                class_model.bases.append(
                    base_name
                )

        # Body de la clase
        body_node = class_node.child_by_field_name("body")

        if body_node is not None:
            for child in body_node.named_children:

                # Imports de clase
                if child.type == "import_statement":
                    import_model = ImportModel(
                        statement=self._get_node_text(child, source),
                        kind="import",
                        scope="class",
                        owner=class_name
                    )

                    class_model.imports.append(import_model)

                elif child.type == "import_from_statement":
                    import_model = ImportModel(
                        statement=self._get_node_text(child, source),
                        kind="from",
                        scope="class",
                        owner=class_name
                    )

                    class_model.imports.append(import_model)

                # Atributos
                elif child.type == "expression_statement":
                    attribute_model = self._read_attribute(
                        child,
                        source
                    )

                    if attribute_model is not None:
                        class_model.attributes.append(
                            attribute_model
                        )

                # Métodos normales
                elif child.type == "function_definition":
                    method_model, method_imports = self._read_function(
                        child,
                        source
                    )

                    class_model.methods.append(
                        method_model
                    )

                # Métodos decorados
                elif child.type == "decorated_definition":
                    definition_node = child.child_by_field_name(
                        "definition"
                    )

                    if (
                        definition_node is not None
                        and definition_node.type == "function_definition"
                    ):
                        method_model, method_imports = self._read_function(
                            definition_node,
                            source
                        )

                        for decorator_node in child.named_children:
                            if decorator_node.type == "decorator":
                                decorator_model = self._read_decorators(
                                    decorator_node,
                                    source
                                )

                                method_model.decorators.append(
                                    decorator_model
                                )

                        class_model.methods.append(
                            method_model
                        )
        return class_model
    
    # extrae la información de un atributo a partir del nodo del árbol de sintaxis
    def _read_attribute(self,node,source: bytes) -> AttributeModel | None:

        if len(node.named_children) == 0:
            return None

        expression_node = node.named_children[0]

        if expression_node.type != "assignment":
            return None

        left_node = expression_node.child_by_field_name("left")
        right_node = expression_node.child_by_field_name("right")
        type_node = expression_node.child_by_field_name("type")

        if left_node is None:
            return None

        attribute_name = self._get_node_text(
            left_node,
            source
        )

        attribute_value = (
            self._get_node_text(right_node, source)
            if right_node is not None
            else None
        )

        type_hint = (
            self._get_node_text(type_node, source)
            if type_node is not None
            else None
        )

        return AttributeModel(
            name=attribute_name,
            type_hint=type_hint,
            value=attribute_value
        )

    def _read_function(self,function_node,source: bytes) -> tuple[FunctionModel, list[ImportModel]]:

        name_node = function_node.child_by_field_name("name")
            
        function_name = self._get_node_text(
            name_node,
            source
        )

        function_model = FunctionModel(
            name=function_name
        )

        function_imports = []

        body_node = function_node.child_by_field_name("body")

        if body_node is not None:
            for child in body_node.named_children:

                if child.type == "import_statement":
                    import_model = ImportModel(
                        statement=self._get_node_text(child, source),
                        kind="import",
                        scope="function",
                        owner=function_name
                    )

                    function_imports.append(import_model)

                elif child.type == "import_from_statement":
                    import_model = ImportModel(
                        statement=self._get_node_text(child, source),
                        kind="from",
                        scope="function",
                        owner=function_name
                    )

                    function_imports.append(import_model)
        # parameters
        parameters_node = function_node.child_by_field_name("parameters")

        if parameters_node is not None:
                for param_node in parameters_node.named_children:
                    parameter_model = self._read_parameter(
                        param_node,
                        source
                    )
    
                    if parameter_model is not None:
                        function_model.parameters.append(parameter_model)
        # return type
        return_type_node = function_node.child_by_field_name("return_type")

        if return_type_node is not None:
            function_model.return_type = self._get_node_text(
                return_type_node,
                source
            )
        # decorators

        return function_model, function_imports

    def _read_decorators(self, decorator_node, source : bytes) -> DecoratorModel:

        statement = self._get_node_text(
            decorator_node,
            source 
        )

        named_children = decorator_node.named_children

        if not named_children:
            return DecoratorModel(
                statement=statement,
                name=statement.lstrip("@")
            )

        expression_node = named_children[0]

        if expression_node.type == "identifier":
            return DecoratorModel(
                statement=statement,
                name=self._get_node_text(
                    expression_node,
                    source
                )
            )

        if expression_node.type == "call":
            function_node = expression_node.child_by_field_name(
                "function"
            )

            arguments_node = expression_node.child_by_field_name(
                "arguments"
            )

            decorator_name = self._get_node_text(
                function_node,
                source
            )

            arguments = []

            if arguments_node is not None:
                for argument_node in arguments_node.named_children:
                    arguments.append(
                        self._get_node_text(
                            argument_node,
                            source
                        )
                    )

            return DecoratorModel(
                statement=statement,
                name=decorator_name,
                arguments=arguments
            )

        return DecoratorModel(
            statement=statement,
            name=self._get_node_text(
                expression_node,
                source
            )
        )
        
    

    def _read_parameter(self,parameter_node,source: bytes) -> ParameterModel | None:
        # nombre
        if parameter_node.type == "identifier":
            return ParameterModel(
                name=self._get_node_text(parameter_node, source)
            )
        # nombre: str
        if parameter_node.type == "typed_parameter":
            name_node = parameter_node.named_children[0]
            type_node = parameter_node.child_by_field_name("type")

            return ParameterModel(
                name=self._get_node_text(name_node, source),
                type_hint=self._get_node_text(type_node, source)
                if type_node is not None
                else None
            )
        # nombre = ""
        if parameter_node.type == "default_parameter":
            name_node = parameter_node.child_by_field_name("name")
            value_node = parameter_node.child_by_field_name("value")

            return ParameterModel(
                name=self._get_node_text(name_node, source),
                default=self._get_node_text(value_node, source)
                if value_node is not None
                else None
            )
        # nombre: str = ""
        if parameter_node.type == "typed_default_parameter":
            name_node = parameter_node.child_by_field_name("name")
            type_node = parameter_node.child_by_field_name("type")
            value_node = parameter_node.child_by_field_name("value")

            return ParameterModel(
                name=self._get_node_text(name_node, source),
                type_hint=self._get_node_text(type_node, source)
                if type_node is not None
                else None,
                default=self._get_node_text(value_node, source)
                if value_node is not None
                else None
            )
        return None
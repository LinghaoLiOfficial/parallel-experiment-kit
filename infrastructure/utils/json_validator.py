import jsonschema

from infrastructure.base.result import Result


class JsonValidator:
    @classmethod
    def check_allowed_output(cls, data, format_check):
        try:
            cls._validate_with_format_check(data=data, rules=format_check)
        except ValueError as exc:
            return Result.build_error_with_results({"errors": str(exc)})
        return Result.build_success()

    @classmethod
    def check_situations(cls, data: dict, schemas: list):
        errors_list = []
        for schema in schemas:
            validate_result = cls.check(data=data, schema=schema)
            if validate_result.status:
                return Result.build_success_with_results({"schema": schema})
            errors_list.append(validate_result.get_data_on_results().get("errors", None))
        return Result.build_error_with_results({"errors_list": errors_list})

    @classmethod
    def check(cls, data: dict, schema: dict):
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            return Result.build_error_with_results({"errors": exc.message})
        return Result.build_success()

    @classmethod
    def _validate_with_format_check(cls, data, rules, path="root"):
        if isinstance(rules, list):
            if not isinstance(data, list):
                raise ValueError(f"{path} must be a list")
            if not rules:
                return
            if all(not isinstance(item, (dict, list)) for item in rules):
                allowed_values = {cls._normalize_scalar(item) for item in rules}
                for index, item in enumerate(data):
                    normalized_item = cls._normalize_scalar(item)
                    if normalized_item not in allowed_values:
                        raise ValueError(
                            f"{path}[{index}] must be one of {sorted(allowed_values)}, got {normalized_item!r}"
                        )
                return
            nested_rule = rules[0]
            for index, item in enumerate(data):
                cls._validate_with_format_check(item, nested_rule, f"{path}[{index}]")
            return

        if isinstance(rules, dict):
            if "__type__" in rules and len(rules) == 1:
                cls._validate_type_rule(data=data, type_name=rules["__type__"], path=path)
                return
            if "__enum__" in rules and len(rules) == 1:
                cls._validate_enum_rule(data=data, allowed_values=rules["__enum__"], path=path)
                return
            if "__list_of__" in rules and len(rules) == 1:
                if not isinstance(data, list):
                    raise ValueError(f"{path} must be a list")
                for index, item in enumerate(data):
                    cls._validate_with_format_check(item, rules["__list_of__"], f"{path}[{index}]")
                return
            if "__any__" in rules and len(rules) == 1:
                return
            if not isinstance(data, dict):
                raise ValueError(f"{path} must be an object")
            for key, rule in rules.items():
                if key not in data:
                    raise ValueError(f"{path}.{key} is required")
                cls._validate_with_format_check(data[key], rule, f"{path}.{key}")
            return

        if isinstance(rules, str) and rules in {"string", "number", "integer", "array", "object", "boolean", "any"}:
            cls._validate_type_rule(data=data, type_name=rules, path=path)
            return

        expected = cls._normalize_scalar(rules)
        actual = cls._normalize_scalar(data)
        if actual != expected:
            raise ValueError(f"{path} must equal {expected!r}, got {actual!r}")

    @staticmethod
    def _normalize_scalar(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if value is None:
            return None
        return str(value)

    @classmethod
    def _validate_enum_rule(cls, data, allowed_values, path):
        normalized_allowed_values = {cls._normalize_scalar(item) for item in allowed_values}
        normalized_data = cls._normalize_scalar(data)
        if normalized_data not in normalized_allowed_values:
            raise ValueError(f"{path} must be one of {sorted(normalized_allowed_values)}, got {normalized_data!r}")

    @staticmethod
    def _validate_type_rule(data, type_name, path):
        type_name = str(type_name).strip().lower()
        if type_name == "any":
            return
        type_checks = {
            "string": lambda value: isinstance(value, str),
            "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
            "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
            "array": lambda value: isinstance(value, list),
            "object": lambda value: isinstance(value, dict),
            "boolean": lambda value: isinstance(value, bool),
        }
        checker = type_checks.get(type_name)
        if checker is None:
            raise ValueError(f"{path} has unsupported type rule {type_name!r}")
        if not checker(data):
            raise ValueError(f"{path} must be of type {type_name}")

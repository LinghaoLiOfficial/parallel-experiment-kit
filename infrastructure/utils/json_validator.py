import jsonschema

from infrastructure.base.result import Result


class JsonValidator:
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

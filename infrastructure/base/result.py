from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    status: bool
    code: int | None = None
    message: str = ""
    body: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "body": self.body,
        }

    def get_data(self, key):
        return self.body.get(key)

    def get_data_on_results(self):
        return self.get_data("results")

    def verify_data(self, key: str):
        value = self.get_data(key)
        if value is None:
            return False
        if hasattr(value, "__len__") and len(value) == 0:
            return False
        return True

    def verify_data_on_results(self):
        return self.verify_data("results")

    @classmethod
    def _build(cls, status: bool, code: int | None, message: str, body: dict[str, Any] | None):
        return cls(status=status, code=code, message=message, body=body or {})

    @classmethod
    def build_success(cls, code: int | None = None, message: str = "", body: dict[str, Any] | None = None):
        return cls._build(True, code, message, body)

    @classmethod
    def build_error(cls, code: int | None = None, message: str = "", body: dict[str, Any] | None = None):
        return cls._build(False, code, message, body)

    @classmethod
    def build_success_with_results(cls, value):
        return cls.build_success(body={"results": value})

    @classmethod
    def build_error_with_results(cls, value):
        return cls.build_error(body={"results": value})

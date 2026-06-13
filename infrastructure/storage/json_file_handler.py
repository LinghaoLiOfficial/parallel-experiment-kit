import json
from pathlib import Path

from infrastructure.base.result import Result
from infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


class JsonFileHandler:
    @classmethod
    def read(cls, file_path):
        try:
            suffix = Path(file_path).suffix.lower()
            with open(file_path, "r", encoding="utf-8") as file:
                if suffix == ".j2":
                    file_data = file.read()
                else:
                    file_data = json.load(file)
        except Exception as exc:
            logger.warning(f"JsonFileHandler read error, e={exc}")
            return Result.build_error()
        return Result.build_success_with_results(file_data)

    @classmethod
    def save(cls, file_path, data):
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as exc:
            logger.warning(f"JsonFileHandler save error, e={exc}")
            return Result.build_error()
        return Result.build_success()

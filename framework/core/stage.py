import os
from abc import ABC, abstractmethod


class BaseStage(ABC):
    name: str = "stage"

    def max_workers(self, context):
        configured = context.config.get("max_workers")
        if configured is not None:
            return configured
        return min(8, os.cpu_count() or 4)

    @abstractmethod
    def prepare(self, context):
        pass

    @abstractmethod
    def get_indices(self, context):
        pass

    @abstractmethod
    def process_row(self, idx, context):
        pass

    @abstractmethod
    def flush_result(self, result, context):
        pass

    def finalize(self, context):
        pass


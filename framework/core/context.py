from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExperimentContext:
    experiment_name: str
    config: dict[str, Any]
    task_id: str | None = None
    result_path: str | None = None
    state: dict[str, Any] = field(default_factory=dict)


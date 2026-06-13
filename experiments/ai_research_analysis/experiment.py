from dataclasses import asdict, dataclass
from pathlib import Path

from framework.core.context import ExperimentContext
from framework.core.experiment import BaseExperiment
from framework.core.runner import PipelineRunner
from infrastructure.config.runtime_config import Config
from infrastructure.llm.llm_service import LLMService
from infrastructure.logging.logger import get_logger, setup_logging

from experiments.ai_research_analysis.stages import AIResearchAnalysisStage


logger = get_logger(__name__)
config = Config()


@dataclass
class AIResearchAnalysisExperimentConfig:
    paper_csv_path: str
    llm_name: str
    llm_version: str
    result_path: str
    analysis_output_data_path: str
    data_info_path: str
    checkpoint_rows: int
    max_rows_per_file: int
    resume: bool
    task_id: str | None = None
    max_paper_num: int | None = None
    to_shuffle: bool = False
    max_workers: int | None = None


class AIResearchAnalysisExperiment(BaseExperiment):
    name = "ai_research_analysis"

    def __init__(self, experiment_config: AIResearchAnalysisExperimentConfig):
        self.experiment_config = experiment_config

    def build_context(self):
        experiment_dict = asdict(self.experiment_config)
        return ExperimentContext(
            experiment_name=self.name,
            config=experiment_dict,
            task_id=experiment_dict.get("task_id"),
            result_path=experiment_dict.get("result_path")
        )

    def build_stages(self):
        return [AIResearchAnalysisStage()]

    def setup(self, context):
        setup_logging()
        context.state["llm_service"] = LLMService()
        context.task_id = self._init_task(context)

    def _init_task(self, context):
        task_id = context.task_id or config.get_uuid()
        logger.info(f"task_id: {task_id}")
        Path(context.result_path).mkdir(parents=True, exist_ok=True)
        return task_id


def run_ai_research_analysis_experiment(experiment_config: AIResearchAnalysisExperimentConfig):
    runner = PipelineRunner()
    experiment = AIResearchAnalysisExperiment(experiment_config=experiment_config)
    return runner.run(experiment)

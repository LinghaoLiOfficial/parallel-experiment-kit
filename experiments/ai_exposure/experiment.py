from dataclasses import dataclass, asdict
from pathlib import Path

from infrastructure.config.runtime_config import Config
from infrastructure.logging.logger import get_logger, setup_logging
from experiments.ai_exposure.knowledge.theme_db_builder import ThemeDBBuilder
from experiments.ai_exposure.stages import (
    AIExposurePhaseOneStage,
    AIExposurePhaseThreeStage,
    AIExposurePhaseTwoStage,
)
from framework.core.context import ExperimentContext
from framework.core.experiment import BaseExperiment
from framework.core.runner import PipelineRunner
from infrastructure.llm.llm_service import LLMService
from experiments.ai_exposure.mappers.ai_exposure_mapper import AIExposureMapper


logger = get_logger(__name__)
config = Config()


@dataclass
class AIExposureExperimentConfig:
    paper_csv_path: str
    openalex_theme_csv_path: str
    committee_theme_xlsx_path: str
    ai_technology_xlsx_path: str
    llm_name: str
    llm_version: str
    result_path: str
    phase_one_output_data_path: str
    phase_two_output_data_path: str
    phase_three_output_data_path: str
    history_methods_path: str
    ai_tech_vector_db_path: str
    history_methods_vector_db_path: str
    data_info_path: str
    ai_tech_distance_threshold: float
    history_methods_distance_threshold: float
    embedding_dimension: int
    checkpoint_rows: int
    max_rows_per_file: int
    resume: bool
    ai_tech_table_path: str
    task_id: str | None = None
    max_paper_num: int | None = None
    rebuild_db: bool = True
    to_judge_openalex_theme: bool = False
    to_judge_committee_theme: bool = False
    to_shuffle: bool = True
    max_workers: int | None = None


class AIExposureExperiment(BaseExperiment):
    name = "ai_exposure"

    def __init__(self, experiment_config: AIExposureExperimentConfig):
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
        return [
            AIExposurePhaseOneStage(),
            AIExposurePhaseTwoStage(),
            AIExposurePhaseThreeStage(),
        ]

    def setup(self, context):
        setup_logging()
        context.state["llm_service"] = LLMService()
        context.task_id = self._init_task(context)

        if context.config["rebuild_db"]:
            ThemeDBBuilder.create_ai_technology_theme_knowledge(
                task_id=context.task_id,
                ai_technology_xlsx_path=context.config["ai_technology_xlsx_path"],
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                ai_tech_vector_db_path=context.config["ai_tech_vector_db_path"],
                embedding_dimension=context.config["embedding_dimension"],
                ai_tech_table_path=context.config["ai_tech_table_path"],
                resume=context.config["resume"]
            )

            if context.config["to_judge_openalex_theme"]:
                ThemeDBBuilder.create_openalex_theme_knowledge(
                    task_id=context.task_id,
                    openalex_theme_csv_path=context.config["openalex_theme_csv_path"]
                )

            if context.config["to_judge_committee_theme"]:
                ThemeDBBuilder.create_committee_theme_knowledge(
                    task_id=context.task_id,
                    committee_theme_xlsx_path=context.config["committee_theme_xlsx_path"]
                )

    def _init_task(self, context):
        task_id = context.task_id or config.get_uuid()
        logger.info(f"task_id: {task_id}")
        Path(context.result_path).mkdir(parents=True, exist_ok=True)
        AIExposureMapper.merge_root_node({"task_id": task_id})
        return task_id


def run_ai_exposure_experiment(experiment_config: AIExposureExperimentConfig):
    runner = PipelineRunner()
    experiment = AIExposureExperiment(experiment_config=experiment_config)
    return runner.run(experiment)

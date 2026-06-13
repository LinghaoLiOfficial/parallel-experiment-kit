from experiments.ai_exposure.experiment import AIExposureExperimentConfig, run_ai_exposure_experiment
from experiments.ai_research_analysis.experiment import (
    AIResearchAnalysisExperimentConfig,
    run_ai_research_analysis_experiment,
)


def run_experiment(experiment_name: str, config: dict):
    if experiment_name == "ai_exposure":
        return run_ai_exposure_experiment(AIExposureExperimentConfig(**config))
    if experiment_name == "ai_research_analysis":
        return run_ai_research_analysis_experiment(AIResearchAnalysisExperimentConfig(**config))
    raise ValueError(f"unsupported experiment: {experiment_name}")

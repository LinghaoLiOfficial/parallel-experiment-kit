import os
from pathlib import Path

# Workaround for duplicated OpenMP runtime (e.g. faiss + other native deps).
# Must be set before importing libraries that may load libomp.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

from infrastructure.app.lifespan import lifespan
from infrastructure.config.app_settings import get_settings

from experiments.registry import run_experiment

settings = get_settings()


if __name__ == '__main__':

    # 初始化全局配置
    lifespan()

    task_id = "e6c1e95d-4f47-4c3d-9f4e-7d6a3d9b2c41"

    paper_csv_path = "data/ai_research_analysis/AI4S_llms_parse_with_openalex_title_abstract.csv"

    result_path = f"result/{task_id}"
    analysis_output_data_path = f"result/{task_id}/analysis_output_data.csv"
    data_info_path = f"result/{task_id}/data_info.json"

    llm_name = "qwen"
    llm_version = "qwen3.6-flash"

    experiment_config = {
        "paper_csv_path": paper_csv_path,
        "llm_name": llm_name,
        "llm_version": llm_version,
        "result_path": result_path,
        "analysis_output_data_path": analysis_output_data_path,
        "data_info_path": data_info_path,
        "checkpoint_rows": 10,
        "max_rows_per_file": 60,
        "resume": True,
        "task_id": task_id,
        "max_paper_num": 60,
        "to_shuffle": False,
        "max_workers": 10,
    }

    run_experiment("ai_research_analysis", experiment_config)

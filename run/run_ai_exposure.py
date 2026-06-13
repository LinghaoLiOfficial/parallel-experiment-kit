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

    task_id = "90d31a26-d934-484a-b69d-5d5936cfe69a"

    paper_csv_path = "data/ai_exposure/shuffled_result01.csv"
    openalex_theme_csv_path = "data/ai_exposure/knowledge_base/1129_openalex学科分类完整版.xlsx"
    committee_theme_xlsx_path = "data/ai_exposure/knowledge_base/基金委代码.docx"
    ai_technology_xlsx_path = "data/ai_exposure/knowledge_base/AI能力值.xlsx"

    result_path = f"result/{task_id}"
    phase_one_output_data_path = f"result/{task_id}/phase_one_output_data.csv"
    phase_two_output_data_path = f"result/{task_id}/phase_two_output_data.csv"
    phase_three_output_data_path = f"result/{task_id}/phase_three_output_data.csv"
    history_methods_path = f"result/{task_id}/history_methods.csv"
    ai_tech_vector_db_path = f"result/{task_id}/ai_tech_vector_db.faiss"
    history_methods_vector_db_path = f"result/{task_id}/history_methods_vector_db.faiss"
    ai_tech_table_path = f"result/{task_id}/ai_tech_table.csv"
    data_info_path = f"result/{task_id}/data_info.json"

    ai_tech_distance_threshold = 0.5
    history_methods_distance_threshold = 0.5

    llm_name = "qwen"
    llm_version = "qwen3.6-flash"

    experiment_config = {
        "paper_csv_path": paper_csv_path,
        "openalex_theme_csv_path": openalex_theme_csv_path,
        "committee_theme_xlsx_path": committee_theme_xlsx_path,
        "ai_technology_xlsx_path": ai_technology_xlsx_path,
        "llm_name": llm_name,
        "llm_version": llm_version,
        "result_path": result_path,
        "phase_one_output_data_path": phase_one_output_data_path,
        "phase_two_output_data_path": phase_two_output_data_path,
        "phase_three_output_data_path": phase_three_output_data_path,
        "history_methods_path": history_methods_path,
        "ai_tech_vector_db_path": ai_tech_vector_db_path,
        "history_methods_vector_db_path": history_methods_vector_db_path,
        "ai_tech_table_path": ai_tech_table_path,
        "data_info_path": data_info_path,
        "ai_tech_distance_threshold": ai_tech_distance_threshold,
        "history_methods_distance_threshold": history_methods_distance_threshold,
        "embedding_dimension": 1024,
        "checkpoint_rows": 10,
        "max_rows_per_file": 20,
        "resume": True,
        "task_id": task_id,
        "max_paper_num": 60,
        "rebuild_db": True,
        "to_judge_openalex_theme": False,
        "to_judge_committee_theme": False,
        "to_shuffle": False,
        "max_workers": 10,
    }

    run_experiment("ai_exposure", experiment_config)

import json

from experiments.ai_exposure.schema import (
    PHASE_ONE_BASE_COLUMNS,
    PHASE_THREE_COLUMNS,
    PHASE_TWO_AI_COLUMNS,
)
from framework.core.stage import BaseStage
from infrastructure.storage.json_file_handler import JsonFileHandler


class AIExposureBaseStage(BaseStage):
    PHASE_ONE_BASE_COLUMNS = PHASE_ONE_BASE_COLUMNS
    PHASE_TWO_AI_COLUMNS = PHASE_TWO_AI_COLUMNS
    PHASE_THREE_COLUMNS = PHASE_THREE_COLUMNS

    def _build_indices(self, cached_processed_num, total_num, max_paper_num):
        upper = total_num if max_paper_num is None else min(total_num, max_paper_num)
        return list(range(cached_processed_num, upper))

    def _load_paper_df(self, context):
        if "filter_col_paper_df" in context.state:
            return context.state["filter_col_paper_df"]

        import pandas as pd

        paper_df = pd.read_csv(context.config["paper_csv_path"], encoding="utf-8", index_col=False)
        if context.config["to_shuffle"]:
            paper_df = paper_df.sample(n=context.config["max_paper_num"]).reset_index(drop=True)

        filter_col_paper_df = paper_df.loc[:, ["title", "full_abstract", "publication_year"]]
        filter_col_paper_df = filter_col_paper_df.rename(columns={"full_abstract": "abstract"})
        context.state["filter_col_paper_df"] = filter_col_paper_df

        JsonFileHandler.save(
            file_path=context.config["data_info_path"],
            data={"paper num": len(filter_col_paper_df)}
        )
        return filter_col_paper_df

    def _llm_service(self, context):
        return context.state["llm_service"]

    def _default_output_result(self, idx, output_data):
        return {"idx": idx, "output_data": output_data}

    @staticmethod
    def to_json(data):
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def phase_one_output_columns(cls):
        return list(cls.PHASE_ONE_BASE_COLUMNS)

    @classmethod
    def phase_two_output_columns(cls):
        return cls.phase_one_output_columns() + list(cls.PHASE_TWO_AI_COLUMNS)

    @classmethod
    def phase_three_output_columns(cls):
        return cls.phase_two_output_columns() + list(cls.PHASE_THREE_COLUMNS)

    @staticmethod
    def normalize_output_data(output_data, columns):
        normalized_data = {}

        for column in columns:
            normalized_data[column] = output_data.get(column, "")

        for key, value in output_data.items():
            if key not in normalized_data:
                normalized_data[key] = value

        return normalized_data

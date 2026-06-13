import json

from experiments.ai_research_analysis.schema import OUTPUT_COLUMNS
from framework.core.stage import BaseStage
from infrastructure.storage.json_file_handler import JsonFileHandler


class AIResearchAnalysisBaseStage(BaseStage):
    OUTPUT_COLUMNS = OUTPUT_COLUMNS

    def _build_indices(self, cached_processed_num, total_num, max_paper_num):
        upper = total_num if max_paper_num is None else min(total_num, max_paper_num)
        return list(range(cached_processed_num, upper))

    def _load_paper_df(self, context):
        if "paper_df" in context.state:
            return context.state["paper_df"]

        import pandas as pd

        paper_df = pd.read_csv(context.config["paper_csv_path"], encoding="utf-8", index_col=False)
        if context.config["to_shuffle"] and context.config["max_paper_num"] is not None:
            paper_df = paper_df.sample(n=min(len(paper_df), context.config["max_paper_num"])).reset_index(drop=True)

        abstract_id_column = None
        for candidate in ["abstract_ID", "abstract_id", "id", "ID", "work_id"]:
            if candidate in paper_df.columns:
                abstract_id_column = candidate
                break

        title_column = None
        for candidate in ["title", "paper_title", "Title", "openalex_title"]:
            if candidate in paper_df.columns:
                title_column = candidate
                break

        abstract_column = None
        for candidate in ["abstract", "full_abstract", "paper_abstract", "Abstract", "openalex_abstract"]:
            if candidate in paper_df.columns:
                abstract_column = candidate
                break

        if abstract_column is None:
            raise ValueError(
                "paper csv must contain one of: abstract, full_abstract, paper_abstract, Abstract, openalex_abstract"
            )

        normalized_df = paper_df.copy()
        if abstract_id_column is None:
            normalized_df["abstract_ID"] = [str(i) for i in range(len(normalized_df))]
        else:
            normalized_df["abstract_ID"] = normalized_df[abstract_id_column].astype(str)

        normalized_df["title"] = normalized_df[title_column].fillna("").astype(str) if title_column else ""
        normalized_df["abstract"] = normalized_df[abstract_column].fillna("").astype(str)
        normalized_df = normalized_df.loc[:, ["abstract_ID", "title", "abstract"]]

        context.state["paper_df"] = normalized_df
        JsonFileHandler.save(
            file_path=context.config["data_info_path"],
            data={"paper_num": len(normalized_df)}
        )
        return normalized_df

    def _llm_service(self, context):
        return context.state["llm_service"]

    def _default_output_result(self, idx, output_data):
        return {"idx": idx, "output_data": output_data}

    @staticmethod
    def to_json(data):
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def output_columns(cls):
        return list(cls.OUTPUT_COLUMNS)

    @staticmethod
    def normalize_output_data(output_data, columns):
        normalized_data = {}
        for column in columns:
            normalized_data[column] = output_data.get(column, "")
        for key, value in output_data.items():
            if key not in normalized_data:
                normalized_data[key] = value
        return normalized_data

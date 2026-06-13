import csv
from pathlib import Path

import pandas as pd

from infrastructure.logging.logger import get_logger
from infrastructure.storage.csv_file_handler import CSVFileHandler

from experiments.ai_research_analysis.stages.base import AIResearchAnalysisBaseStage


logger = get_logger(__name__)

AI_USE_LABEL_TO_CODE = {
    "expert systems": 0,
    "knowledge representation": 1,
    "computer vision": 2,
    "machine learning": 3,
    "deep learning": 4,
    "evolutionary computation": 5,
    "natural language processing": 6,
    "large language models": 7,
    "reinforcement learning": 8,
    "embodied intelligence/robotics": 9,
    "none": "none",
}

AI_USE_ALIASES = {
    "0": "expert systems",
    "1": "knowledge representation",
    "2": "computer vision",
    "3": "machine learning",
    "4": "deep learning",
    "5": "evolutionary computation",
    "6": "natural language processing",
    "7": "large language models",
    "8": "reinforcement learning",
    "9": "embodied intelligence/robotics",
    "expert systems": "expert systems",
    "knowledge representation": "knowledge representation",
    "computer vision": "computer vision",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "evolutionary computation": "evolutionary computation",
    "natural language processing": "natural language processing",
    "large language models": "large language models",
    "reinforcement learning": "reinforcement learning",
    "embodied intelligence/robotics": "embodied intelligence/robotics",
    "robotics": "embodied intelligence/robotics",
    "专家系统": "expert systems",
    "知识表示": "knowledge representation",
    "计算机视觉": "computer vision",
    "机器学习": "machine learning",
    "深度学习": "deep learning",
    "进化计算": "evolutionary computation",
    "自然语言处理": "natural language processing",
    "大语言模型": "large language models",
    "强化学习": "reinforcement learning",
    "具身智能/机器人": "embodied intelligence/robotics",
    "机器人": "embodied intelligence/robotics",
    "none": "none",
}

AI_FUNCTION_LABEL_TO_CODE = {
    "information retrieval and extraction": 0,
    "phenomenon detection/monitoring": 1,
    "clustering and classification": 2,
    "reasoning/inference": 3,
    "estimation, simulation, and prediction": 4,
    "decision-making and optimization": 5,
    "process acceleration": 6,
    "content generation": 7,
    "none": "none",
}

AI_FUNCTION_ALIASES = {
    "0": "information retrieval and extraction",
    "1": "phenomenon detection/monitoring",
    "2": "clustering and classification",
    "3": "reasoning/inference",
    "4": "estimation, simulation, and prediction",
    "5": "decision-making and optimization",
    "6": "process acceleration",
    "7": "content generation",
    "information retrieval and extraction": "information retrieval and extraction",
    "phenomenon detection/monitoring": "phenomenon detection/monitoring",
    "clustering and classification": "clustering and classification",
    "reasoning/inference": "reasoning/inference",
    "estimation, simulation, and prediction": "estimation, simulation, and prediction",
    "decision-making and optimization": "decision-making and optimization",
    "process acceleration": "process acceleration",
    "content generation": "content generation",
    "信息检索与提取": "information retrieval and extraction",
    "现象检测/监测": "phenomenon detection/monitoring",
    "聚类与分类": "clustering and classification",
    "推理/推断": "reasoning/inference",
    "估计、模拟与预测": "estimation, simulation, and prediction",
    "决策与优化": "decision-making and optimization",
    "流程加速": "process acceleration",
    "内容生成": "content generation",
    "none": "none",
}

AI_ROLE_LABEL_TO_CODE = {
    "domain facilitator": 1,
    "method upgrader": 2,
    "episteme expander": 3,
    "none": 0,
}

AI_ROLE_ALIASES = {
    "0": "none",
    "1": "domain facilitator",
    "2": "method upgrader",
    "3": "episteme expander",
    "domain facilitator": "domain facilitator",
    "method upgrader": "method upgrader",
    "episteme expander": "episteme expander",
    "赋能应用": "domain facilitator",
    "工具方法": "method upgrader",
    "认识知识": "episteme expander",
    "none": "none",
}

PHASE_FIELD_MAPPING = {
    "hypothesis generation": "hypothesis_AI_use",
    "experimental analysis": "experiment_AI_use",
    "data processing": "data_AI_use",
    "result analysis": "result_AI_use",
    "假设生成": "hypothesis_AI_use",
    "实验分析": "experiment_AI_use",
    "数据处理": "data_AI_use",
    "结果分析": "result_AI_use",
}


class AIResearchAnalysisStage(AIResearchAnalysisBaseStage):
    name = "analysis"

    def prepare(self, context):
        self.paper_df = self._load_paper_df(context)
        self.output_data_file_handler = CSVFileHandler(
            save_path=context.config["analysis_output_data_path"],
            write_mode="a",
            checkpoint_rows=context.config["checkpoint_rows"],
            max_rows_per_file=context.config["max_rows_per_file"],
            resume=context.config["resume"]
        )

    def get_indices(self, context):
        return self._build_indices(
            self.output_data_file_handler.processed_num,
            len(self.paper_df),
            context.config["max_paper_num"]
        )

    def process_row(self, idx, context):
        row = self.paper_df.loc[idx]
        output_data = self._build_default_output_data(
            abstract_id=str(row["abstract_ID"]),
            paper_title=row["title"],
            paper_abstract=row["abstract"],
        )
        llm_service = self._llm_service(context)

        try:
            parse_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisPrompt.j2",
                format_check_path="experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisFormatCheck.json",
                input_params={
                    "abstract_ID": str(row["abstract_ID"]),
                    "paper_title": row["title"],
                    "paper_abstract": row["abstract"],
                },
                lang="en"
            )
            if not parse_result.status:
                logger.warning(f"abstract ai research analysis error, idx={idx}")
                return self._default_output_result(idx, output_data)

            result = self._normalize_result_payload(parse_result.get_data_on_results())
            phase_mapping = result.get("phase_ai_usage", {})
            for phase_name, field_name in PHASE_FIELD_MAPPING.items():
                output_data[field_name] = self._normalize_single_label(
                    phase_mapping.get(phase_name, "none"),
                    AI_USE_ALIASES,
                    default="none"
                )

            ai_functions = result.get("ai_functions", ["none"])
            if not ai_functions:
                ai_functions = ["none"]
            output_data["AI_function"] = self._serialize_multi_value(
                self._map_labels(
                    ai_functions,
                    AI_FUNCTION_ALIASES,
                    AI_FUNCTION_LABEL_TO_CODE,
                    allow_multi=True,
                    default_values=["none"],
                )
            )

            ai_roles = result.get("ai_role", ["none"])
            if not ai_roles:
                ai_roles = ["none"]
            output_data["ai_role"] = self._serialize_multi_value(
                self._map_labels(
                    ai_roles,
                    AI_ROLE_ALIASES,
                    AI_ROLE_LABEL_TO_CODE,
                    allow_multi=True,
                    default_values=[0],
                )
            )
            output_data["ai_role_sentence"] = self._serialize_sentences(result.get("ai_role_sentence", []))

            essentiality = self._normalize_essentiality(result.get("essentiality", 0))
            output_data["essentiality"] = essentiality
            output_data["essentiality_sentence"] = self._serialize_sentences(result.get("essentiality_sentence", []))
            self._normalize_consistency(output_data)

            return self._default_output_result(idx, output_data)
        except Exception as exc:
            logger.warning(f"analysis stage error, idx={idx}, e={exc}")
            return self._default_output_result(idx, output_data)

    @staticmethod
    def _build_default_output_data(abstract_id, paper_title, paper_abstract):
        return {
            "abstract_ID": str(abstract_id),
            "paper_title": paper_title,
            "paper_abstract": paper_abstract,
            "hypothesis_AI_use": "none",
            "experiment_AI_use": "none",
            "data_AI_use": "none",
            "result_AI_use": "none",
            "AI_function": "none",
            "ai_role": 0,
            "ai_role_sentence": "",
            "essentiality": 0,
            "essentiality_sentence": "",
        }

    @classmethod
    def _normalize_result_payload(cls, result):
        if not isinstance(result, dict):
            return {
                "phase_ai_usage": {},
                "ai_functions": ["none"],
                "ai_role": ["none"],
                "ai_role_sentence": [],
                "essentiality": 0,
                "essentiality_sentence": [],
            }

        phase_ai_usage = result.get("phase_ai_usage", {})
        if not isinstance(phase_ai_usage, dict):
            phase_ai_usage = {}

        normalized_phase_ai_usage = {}
        for phase_name, field_name in PHASE_FIELD_MAPPING.items():
            if field_name in normalized_phase_ai_usage:
                continue
            normalized_phase_ai_usage[phase_name] = phase_ai_usage.get(phase_name, "none")

        return {
            "phase_ai_usage": normalized_phase_ai_usage,
            "ai_functions": cls._ensure_list(result.get("ai_functions", ["none"]), fallback=["none"]),
            "ai_role": cls._ensure_list(result.get("ai_role", ["none"]), fallback=["none"]),
            "ai_role_sentence": cls._ensure_list(result.get("ai_role_sentence", []), fallback=[]),
            "essentiality": result.get("essentiality", 0),
            "essentiality_sentence": cls._ensure_list(result.get("essentiality_sentence", []), fallback=[]),
        }

    def flush_result(self, result, context):
        idx = result["idx"]
        normalized_output_data = self.normalize_output_data(
            result["output_data"],
            self.output_columns(),
        )
        self.output_data_file_handler.save(normalized_output_data)
        logger.info(f"{idx} {result['output_data'].get('abstract_ID', 'unknown')} has been parsed successfully")

    def finalize(self, context):
        self.output_data_file_handler.save()
        self._export_final_artifacts(context)
        logger.info("finished ai research analysis")

    @staticmethod
    def _map_labels(labels, alias_mapping, value_mapping, allow_multi=False, default_values=None):
        normalized = []
        for label in labels:
            canonical_label = AIResearchAnalysisStage._normalize_single_label(label, alias_mapping, default=None)
            if canonical_label is None or canonical_label not in value_mapping:
                continue
            normalized.append(value_mapping[canonical_label])
        if not normalized:
            if default_values is not None:
                return default_values if allow_multi else default_values[0]
            return ["none"] if allow_multi else "none"
        deduped = []
        for item in normalized:
            if item not in deduped:
                deduped.append(item)
        if allow_multi:
            return deduped
        return deduped[0]

    @staticmethod
    def _serialize_multi_value(values):
        if isinstance(values, list):
            if not values:
                return "none"
            if len(values) == 1:
                return str(values[0])
            return ",".join(str(v) for v in values)
        return str(values)

    @staticmethod
    def _serialize_sentences(sentences):
        if not sentences:
            return ""
        return " || ".join(str(sentence).strip() for sentence in sentences if str(sentence).strip())

    @staticmethod
    def _normalize_consistency(output_data):
        if str(output_data.get("ai_role", "0")).strip() == "0":
            output_data["ai_role_sentence"] = ""
        if int(output_data.get("essentiality", 0)) == 0:
            output_data["essentiality_sentence"] = ""

    @staticmethod
    def _normalize_single_label(value, alias_mapping, default="none"):
        if value is None:
            return default
        cleaned = str(value).strip()
        return alias_mapping.get(cleaned, default)

    @staticmethod
    def _normalize_essentiality(value):
        try:
            score = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(5, score))

    @staticmethod
    def _is_missing(value):
        if value is None:
            return True
        try:
            if pd.isna(value):
                return True
        except Exception:
            pass
        cleaned = str(value).strip().lower()
        return cleaned in {"", "nan", "none", "null"}

    @classmethod
    def _ensure_list(cls, value, fallback):
        if cls._is_missing(value):
            return list(fallback)
        if isinstance(value, list):
            cleaned_values = [item for item in value if not cls._is_missing(item)]
            return cleaned_values if cleaned_values else list(fallback)
        if isinstance(value, tuple):
            cleaned_values = [item for item in value if not cls._is_missing(item)]
            return cleaned_values if cleaned_values else list(fallback)
        return [value]

    def _export_final_artifacts(self, context):
        df = self.output_data_file_handler.read()
        if df.empty:
            return

        result_dir = Path(context.config["result_path"])
        result_dir.mkdir(parents=True, exist_ok=True)

        task1_df = df.loc[:, [
            "abstract_ID",
            "hypothesis_AI_use",
            "experiment_AI_use",
            "data_AI_use",
            "result_AI_use",
        ]].copy()
        task1_csv_path = result_dir / "task1_phase_ai_usage.csv"
        task1_df.to_csv(task1_csv_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
        self._write_text(
            result_dir / "task1_phase_ai_usage.txt",
            self._render_task1_text(task1_df)
        )
        self._write_text(
            result_dir / "task1_phase_ai_usage.md",
            task1_df.to_markdown(index=False)
        )

        task2_df = df.loc[:, ["abstract_ID", "AI_function"]].copy()
        task2_csv_path = result_dir / "task2_ai_function.csv"
        task2_df.to_csv(task2_csv_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
        self._write_text(
            result_dir / "task2_ai_function.txt",
            self._render_task2_text(task2_df)
        )
        self._write_text(
            result_dir / "task2_ai_function.md",
            task2_df.to_markdown(index=False)
        )

        task3_df = df.loc[:, ["abstract_ID", "ai_role", "ai_role_sentence"]].copy()
        task3_df = task3_df.rename(columns={"ai_role_sentence": "sentence"})
        task3_df.to_csv(result_dir / "task3_ai_role.csv", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

        task4_df = df.loc[:, ["abstract_ID", "essentiality", "essentiality_sentence"]].copy()
        task4_df = task4_df.rename(columns={"essentiality_sentence": "sentence"})
        task4_df.to_csv(result_dir / "task4_essentiality.csv", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

        review_df = self._build_missing_evidence_review_df(df)
        review_df.to_csv(
            result_dir / "review_positive_without_evidence.csv",
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_MINIMAL
        )
        self._write_text(
            result_dir / "review_positive_without_evidence.md",
            review_df.to_markdown(index=False) if not review_df.empty else "| status |\n| --- |\n| no rows |"
        )

    @staticmethod
    def _write_text(path, content):
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _render_task1_text(df: pd.DataFrame):
        blocks = []
        for row in df.to_dict(orient="records"):
            blocks.append(
                "\n".join([
                    f"-{row['abstract_ID']}",
                    f"[假设生成]：{row['hypothesis_AI_use']}",
                    f"[实验分析]：{row['experiment_AI_use']}",
                    f"[数据处理]：{row['data_AI_use']}",
                    f"[结果分析]：{row['result_AI_use']}",
                ])
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _render_task2_text(df: pd.DataFrame):
        lines = []
        for row in df.to_dict(orient="records"):
            lines.append(f"-{row['abstract_ID']}：{row['AI_function']}")
        return "\n".join(lines)

    @staticmethod
    def _build_missing_evidence_review_df(df: pd.DataFrame):
        review_rows = []
        for row in df.to_dict(orient="records"):
            ai_role_value = str(row.get("ai_role", "")).strip()
            ai_role_sentence = row.get("ai_role_sentence", "")
            essentiality_raw = row.get("essentiality", 0)
            essentiality_sentence = row.get("essentiality_sentence", "")

            try:
                essentiality_value = int(float(essentiality_raw))
            except (TypeError, ValueError):
                essentiality_value = 0

            positive_ai_role = ai_role_value not in {"", "0", "none", "nan"}
            positive_essentiality = essentiality_value > 0

            if positive_ai_role and AIResearchAnalysisStage._is_missing(ai_role_sentence):
                review_rows.append({
                    "abstract_ID": row.get("abstract_ID", ""),
                    "paper_title": row.get("paper_title", ""),
                    "review_type": "ai_role_missing_evidence",
                    "positive_value": ai_role_value,
                    "existing_phase_labels": "|".join([
                        str(row.get("hypothesis_AI_use", "")),
                        str(row.get("experiment_AI_use", "")),
                        str(row.get("data_AI_use", "")),
                        str(row.get("result_AI_use", "")),
                    ]),
                    "AI_function": row.get("AI_function", ""),
                    "paper_abstract": row.get("paper_abstract", ""),
                })

            if positive_essentiality and AIResearchAnalysisStage._is_missing(essentiality_sentence):
                review_rows.append({
                    "abstract_ID": row.get("abstract_ID", ""),
                    "paper_title": row.get("paper_title", ""),
                    "review_type": "essentiality_missing_evidence",
                    "positive_value": essentiality_value,
                    "existing_phase_labels": "|".join([
                        str(row.get("hypothesis_AI_use", "")),
                        str(row.get("experiment_AI_use", "")),
                        str(row.get("data_AI_use", "")),
                        str(row.get("result_AI_use", "")),
                    ]),
                    "AI_function": row.get("AI_function", ""),
                    "paper_abstract": row.get("paper_abstract", ""),
                })

        return pd.DataFrame(
            review_rows,
            columns=[
                "abstract_ID",
                "paper_title",
                "review_type",
                "positive_value",
                "existing_phase_labels",
                "AI_function",
                "paper_abstract",
            ]
        )

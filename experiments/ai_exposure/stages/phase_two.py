import json

from infrastructure.logging.logger import get_logger
from infrastructure.storage.csv_file_handler import CSVFileHandler

from experiments.ai_exposure.stages.base import AIExposureBaseStage


logger = get_logger(__name__)


class AIExposurePhaseTwoStage(AIExposureBaseStage):
    name = "phase_two"

    def prepare(self, context):
        self.filter_col_paper_df = self._load_paper_df(context)
        self.phase_one_output_data_file_handler = CSVFileHandler(
            save_path=context.config["phase_one_output_data_path"],
            write_mode="a",
            checkpoint_rows=context.config["checkpoint_rows"],
            max_rows_per_file=context.config["max_rows_per_file"],
            resume=context.config["resume"]
        )
        self.phase_one_result_df = self.phase_one_output_data_file_handler.read()
        self.output_data_file_handler = CSVFileHandler(
            save_path=context.config["phase_two_output_data_path"],
            write_mode="a",
            checkpoint_rows=context.config["checkpoint_rows"],
            max_rows_per_file=context.config["max_rows_per_file"],
            resume=context.config["resume"]
        )

    def get_indices(self, context):
        return self._build_indices(
            self.output_data_file_handler.processed_num,
            len(self.filter_col_paper_df),
            context.config["max_paper_num"]
        )

    def process_row(self, idx, context):
        output_data = self.phase_one_result_df.iloc[idx, :].to_dict()
        llm_service = self._llm_service(context)
        try:
            paper_title = self.filter_col_paper_df.loc[idx, "title"]
            paper_abstract = self.filter_col_paper_df.loc[idx, "abstract"]

            if self.phase_one_result_df.loc[idx, "review_paper_judgment"] == "yes":
                logger.info(f"skip review paper, idx={idx}, paper_title={paper_title}")
                return self._default_output_result(idx, output_data)

            if isinstance(self.phase_one_result_df.loc[idx, "research_task_phase_mapping"], float):
                logger.info(f"skip not related paper, idx={idx}, paper_title={paper_title}")
                return self._default_output_result(idx, output_data)

            no_ai_mark = True
            research_task_phase_mapping = json.loads(self.phase_one_result_df.loc[idx, "research_task_phase_mapping"])
            for phase in research_task_phase_mapping.values():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    no_ai_mark = False
                    break
            if no_ai_mark:
                output_data.update({
                    "ai_usage_rate": 0,
                    "ai_irreplaceable_score": 0,
                    "fully_based_on_ai": 0,
                    "partially_based_on_ai": 0,
                })
                return self._default_output_result(idx, output_data)

            ai_role_assessment_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                template_path="experiments/ai_exposure/llm/AIRoleAssessment/AIRoleAssessmentTemplate.json",
                schemas_path="experiments/ai_exposure/llm/AIRoleAssessment/AIRoleAssessmentSchemas.json",
                input_params={"paper_title": paper_title, "paper_abstract": paper_abstract},
                lang="en"
            )
            if not ai_role_assessment_result.status:
                logger.warning(f"ai_role_assessment_result error, idx={idx}, ai_role_assessment_result={ai_role_assessment_result.to_dict()}")
                return self._default_output_result(idx, output_data)

            ai_role_assessment = ai_role_assessment_result.get_data_on_results()
            output_data["ai_necessity"] = ai_role_assessment.get("ai_necessity", "")
            output_data["ai_necessity_reason"] = ai_role_assessment.get("ai_necessity_reason", "")
            output_data["ai_usage_level"] = ai_role_assessment.get("ai_usage_level", "")
            output_data["ai_usage_level_reason"] = ai_role_assessment.get("ai_usage_level_reason", "")

            if ai_role_assessment["ai_necessity"] == "indispensable":
                output_data.update({
                    "ai_usage_rate": 1,
                    "ai_irreplaceable_score": 1,
                    "fully_based_on_ai": 0,
                    "partially_based_on_ai": 0,
                })
                return self._default_output_result(idx, output_data)

            if ai_role_assessment["ai_usage_level"] == "fully_based":
                output_data.update({
                    "ai_usage_rate": 1,
                    "ai_irreplaceable_score": 0,
                    "fully_based_on_ai": 1,
                    "partially_based_on_ai": 0,
                })
                return self._default_output_result(idx, output_data)

            output_data.update({
                "ai_usage_rate": 1,
                "ai_irreplaceable_score": 0,
                "fully_based_on_ai": 0,
                "partially_based_on_ai": 1,
            })
            total_score = sum([phase["ranking"] for phase in research_task_phase_mapping.values()])
            ai_usage_rate = 0.0
            for phase in research_task_phase_mapping.values():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    ai_usage_rate += float(phase["ranking"]) / float(total_score)

            output_data["ai_usage_rate"] = ai_usage_rate
            return self._default_output_result(idx, output_data)
        except Exception as e:
            logger.warning(f"phase two error, idx={idx}, e={e}")
            return self._default_output_result(idx, output_data)

    def flush_result(self, result, context):
        idx = result["idx"]
        normalized_output_data = self.normalize_output_data(
            result["output_data"],
            self.phase_two_output_columns(),
        )
        self.output_data_file_handler.save(normalized_output_data)
        logger.info(f"{idx} {result['output_data'].get('paper_title', 'unknown')} has been parsed successfully")

    def finalize(self, context):
        self.output_data_file_handler.save()
        logger.info("finished parsing papers phase two")

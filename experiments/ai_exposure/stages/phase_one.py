from infrastructure.logging.logger import get_logger
from infrastructure.storage.csv_file_handler import CSVFileHandler
from infrastructure.utils.path_utils import StrGenerator
from infrastructure.vector.faiss_vector_db_driver import FAISSVectorDBDriver

from experiments.ai_exposure.knowledge.theme_extractor import ThemeExtractor
from experiments.ai_exposure.stages.base import AIExposureBaseStage


logger = get_logger(__name__)


class AIExposurePhaseOneStage(AIExposureBaseStage):
    name = "phase_one"

    def prepare(self, context):
        self.filter_col_paper_df = self._load_paper_df(context)
        self.output_data_file_handler = CSVFileHandler(
            save_path=context.config["phase_one_output_data_path"],
            write_mode="a",
            checkpoint_rows=context.config["checkpoint_rows"],
            max_rows_per_file=context.config["max_rows_per_file"],
            resume=context.config["resume"]
        )
        self.history_methods_file_handler = CSVFileHandler(
            save_path=context.config["history_methods_path"],
            write_mode="a",
            checkpoint_rows=context.config["checkpoint_rows"],
            max_rows_per_file=context.config["max_rows_per_file"],
            resume=context.config["resume"]
        )
        self.faiss_driver = FAISSVectorDBDriver(
            file_save_path=context.config["history_methods_vector_db_path"],
            dimension=context.config["embedding_dimension"],
            index_type="flat_ip",
            resume=True
        )

    def get_indices(self, context):
        return self._build_indices(
            self.output_data_file_handler.processed_num,
            len(self.filter_col_paper_df),
            context.config["max_paper_num"]
        )

    def process_row(self, idx, context):
        output_data = {}
        llm_service = self._llm_service(context)
        try:
            paper_title = self.filter_col_paper_df.loc[idx, "title"]
            paper_abstract = self.filter_col_paper_df.loc[idx, "abstract"]
            publication_year = self.filter_col_paper_df.loc[idx, "publication_year"]
            output_data["paper_title"] = paper_title
            output_data["paper_abstract"] = paper_abstract
            output_data["publication_year"] = publication_year

            filter_review_paper_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/FilterReviewPaper/FilterReviewPaperPrompt.j2",
                format_check_path="experiments/ai_exposure/llm/FilterReviewPaper/FilterReviewPaperFormatCheck.json",
                input_params={"paper_title": paper_title, "paper_abstract": paper_abstract},
                lang="en"
            )
            if not filter_review_paper_result.status:
                logger.warning(f"filter_review_paper error, idx={idx}, filter_review_paper_result={filter_review_paper_result.to_dict()}")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            filter_review = filter_review_paper_result.get_data_on_results()
            output_data["review_paper_judgment"] = filter_review.get("judgment", "")
            output_data["review_paper_reason"] = filter_review.get("reason", "")

            if output_data["review_paper_judgment"] == "yes":
                logger.info(f"skip review paper, idx={idx}, paper_title={paper_title}")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            if context.config["to_judge_openalex_theme"]:
                openalex_theme_extractor = ThemeExtractor()
                openalex_theme_extractor.recursion_fetch_and_rank(
                    node_idx=0,
                    value=context.task_id,
                    paper_title=paper_title,
                    paper_abstract=paper_abstract,
                    ahead_level=1,
                    belong="openalex"
                )
                output_data["openalex_theme_classification"] = str(openalex_theme_extractor.theme_result)

            if context.config["to_judge_committee_theme"]:
                committee_theme_extractor = ThemeExtractor()
                committee_theme_extractor.recursion_fetch_and_rank(
                    node_idx=0,
                    value=context.task_id,
                    paper_title=paper_title,
                    paper_abstract=paper_abstract,
                    ahead_level=3,
                    belong="committee"
                )
                output_data["committee_theme_classification"] = str(committee_theme_extractor.theme_result)

            macro_paradigm_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/MacroParadigm/MacroParadigmPrompt.j2",
                format_check_path="experiments/ai_exposure/llm/MacroParadigm/MacroParadigmFormatCheck.json",
                input_params={"paper_title": paper_title, "paper_abstract": paper_abstract},
                lang="en"
            )
            if not macro_paradigm_result.status:
                logger.warning(f"macro_paradigm error, idx={idx}, macro_paradigm_result={macro_paradigm_result.to_dict()}")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            macro_paradigm = macro_paradigm_result.get_data_on_results()
            output_data["macro_paradigm_judgment"] = macro_paradigm.get("judgment", "")
            output_data["macro_paradigm_reason"] = macro_paradigm.get("reason", "")

            core_research_question_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/CoreResearchQuestion/CoreResearchQuestionPrompt.j2",
                format_check_path="experiments/ai_exposure/llm/CoreResearchQuestion/CoreResearchQuestionFormatCheck.json",
                input_params={"paper_title": paper_title, "paper_abstract": paper_abstract},
                lang="en"
            )
            if not core_research_question_result.status:
                logger.warning(f"core_research_question error, idx={idx}, core_research_question_result={core_research_question_result.to_dict()}")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            core_research_question = core_research_question_result.get_data_on_results()
            output_data["core_research_question_judgment"] = core_research_question.get("core_research_question", "")
            output_data["core_research_question_reason"] = core_research_question.get("reason", "")
            output_data["core_research_question_energy_transition_related"] = core_research_question.get("energy_transition_related", "")
            output_data["core_research_question_climate_change_related"] = core_research_question.get("climate_change_related", "")

            if (core_research_question["energy_transition_related"] != "yes") and (
                core_research_question["climate_change_related"] != "yes"
            ):
                logger.info(f"{paper_title} not related")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            research_task_phase_mapping_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/ResearchTaskPhaseMapping/ResearchTaskPhaseMappingPrompt.j2",
                format_check_path="experiments/ai_exposure/llm/ResearchTaskPhaseMapping/ResearchTaskPhaseMappingFormatCheck.json",
                input_params={"paper_title": paper_title, "paper_abstract": paper_abstract},
                lang="en"
            )
            if not research_task_phase_mapping_result.status:
                logger.warning(f"research_task_phase_mapping error, idx={idx}, research_task_phase_mapping_result={research_task_phase_mapping_result.to_dict()}")
                return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

            research_task_phase_mapping = research_task_phase_mapping_result.get_data_on_results()["phase_mapping"]
            output_data["research_task_phase_mapping"] = self.to_json(research_task_phase_mapping)

            use_ai_phases = []
            for phase_name, phase in research_task_phase_mapping.items():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    use_ai_phases.append(phase_name)
            output_data["use_ai_phases"] = use_ai_phases

            use_ai_mark = False
            for phase in research_task_phase_mapping.values():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    use_ai_mark = True
                    break

            if not use_ai_mark:
                tools_methods = {}
                tools_methods_ids = {}
                pending_history_vectors = []
                for phase_name in research_task_phase_mapping.keys():
                    tools_methods[phase_name] = research_task_phase_mapping[phase_name]["tools_methods"]
                    tools_method_id = StrGenerator.generate_uuid()
                    parse_embeddings_result = llm_service.parse_embeddings(
                        texts=[tools_methods[phase_name]],
                        dimensions=context.config["embedding_dimension"],
                        batch_size=10
                    )
                    if not parse_embeddings_result.status:
                        logger.warning(f"parse_embeddings func error, parse_embeddings_result={parse_embeddings_result.to_dict()}")
                        return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

                    embedding_vectors_array = parse_embeddings_result.get_data_on_results()
                    pending_history_vectors.append((embedding_vectors_array, tools_method_id))
                    tools_methods_ids[phase_name] = tools_method_id

                return {
                    "idx": idx,
                    "output_data": output_data,
                    "history_row": {"paper_title": paper_title, "tools_methods": tools_methods, "tools_methods_ids": tools_methods_ids},
                    "pending_history_vectors": pending_history_vectors,
                }

            return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}
        except Exception as e:
            logger.warning(f"phase one error, idx={idx}, e={e}")
            return {"idx": idx, "output_data": output_data, "history_row": None, "pending_history_vectors": []}

    def flush_result(self, result, context):
        idx = result["idx"]
        for embedding_vectors_array, tools_method_id in result["pending_history_vectors"]:
            self.faiss_driver.insert(vectors=embedding_vectors_array, ids=[tools_method_id])
        if result["history_row"] is not None:
            self.history_methods_file_handler.save(result["history_row"])
        normalized_output_data = self.normalize_output_data(
            result["output_data"],
            self.phase_one_output_columns(),
        )
        self.output_data_file_handler.save(normalized_output_data)
        logger.info(f"{idx} {result['output_data'].get('paper_title', 'unknown')} has been parsed successfully")

    def finalize(self, context):
        self.faiss_driver.save()
        self.history_methods_file_handler.save()
        self.output_data_file_handler.save()
        logger.info("finished parsing papers phase one")

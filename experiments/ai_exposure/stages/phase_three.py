import copy
import json

from infrastructure.logging.logger import get_logger
from infrastructure.storage.csv_file_handler import CSVFileHandler
from infrastructure.vector.faiss_vector_db_driver import FAISSVectorDBDriver

from experiments.ai_exposure.stages.base import AIExposureBaseStage
from experiments.ai_exposure.mappers.ai_exposure_mapper import AIExposureMapper


logger = get_logger(__name__)


class AIExposurePhaseThreeStage(AIExposureBaseStage):
    name = "phase_three"

    def prepare(self, context):
        self.filter_col_paper_df = self._load_paper_df(context)
        self.phase_two_output_data_file_handler = CSVFileHandler(
            save_path=context.config["phase_two_output_data_path"],
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
        self.phase_two_result_df = self.phase_two_output_data_file_handler.read()
        self.history_methods_db_df = self.history_methods_file_handler.read()
        self.history_methods_faiss_driver = FAISSVectorDBDriver(
            file_save_path=context.config["history_methods_vector_db_path"],
            dimension=context.config["embedding_dimension"],
            index_type="flat_ip",
            resume=True
        )
        self.ai_tech_faiss_driver = FAISSVectorDBDriver(
            file_save_path=context.config["ai_tech_vector_db_path"],
            dimension=context.config["embedding_dimension"],
            index_type="flat_ip",
            resume=True
        )
        self.output_data_file_handler = CSVFileHandler(
            save_path=context.config["phase_three_output_data_path"],
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
        output_data = self.phase_two_result_df.iloc[idx, :].to_dict()
        llm_service = self._llm_service(context)
        try:
            paper_title = self.filter_col_paper_df.loc[idx, "title"]
            publication_year = self.filter_col_paper_df.loc[idx, "publication_year"]

            if isinstance(self.phase_two_result_df.loc[idx, "core_research_question_judgment"], float):
                logger.info(f"skip review paper, idx={idx}, paper_title={paper_title}")
                return self._default_output_result(idx, output_data)

            if self.phase_two_result_df.loc[idx, "review_paper_judgment"] == "yes":
                logger.info(f"skip review paper, idx={idx}, paper_title={paper_title}")
                return self._default_output_result(idx, output_data)

            if self.phase_two_result_df.loc[idx, "ai_irreplaceable_score"] == 1:
                output_data["ai_exposure_rate"] = 1
                return self._default_output_result(idx, output_data)

            ai_research_task_phase_mapping_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/AIDesignResearchTaskPhaseMapping/AIDesignResearchTaskPhaseMappingPrompt.j2",
                format_check_path="experiments/ai_exposure/llm/AIDesignResearchTaskPhaseMapping/AIDesignResearchTaskPhaseMappingFormatCheck.json",
                input_params={"research_question": self.phase_two_result_df.loc[idx, "core_research_question_judgment"]},
                lang="en"
            )
            if not ai_research_task_phase_mapping_result.status:
                logger.warning(f"ai_research_task_phase_mapping error, idx={idx}, ai_research_task_phase_mapping_result={ai_research_task_phase_mapping_result.to_dict()}")
                return self._default_output_result(idx, output_data)

            ai_research_task_phase_mapping = ai_research_task_phase_mapping_result.get_data_on_results()["phase_mapping"]
            output_data["ai_research_task_phase_mapping_result"] = self.to_json(ai_research_task_phase_mapping)

            ai_research_use_ai_phases = []
            for phase_name, phase in ai_research_task_phase_mapping.items():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    ai_research_use_ai_phases.append(phase_name)
            output_data["ai_research_use_ai_phases"] = ai_research_use_ai_phases

            matched_ai_research_task_phase_mapping = copy.deepcopy(ai_research_task_phase_mapping)
            neo4j_result = AIExposureMapper.match_all_tech_en_name_and_keyword_list_mappings({"task_id": context.task_id})
            tech_node_list = []
            if neo4j_result.verify_data_on_results():
                tech_node_list = [x["e"] for x in neo4j_result.get_data_on_results()]

            ai_tech_id_to_info_mapping = {}
            for node in tech_node_list:
                for index, item_id in enumerate(node["keyword_id_list"]):
                    ai_tech_id_to_info_mapping[item_id] = {
                        "ai_tech_keyword": node["keyword_list"][index],
                        "ai_tech": node["tech_en_name"],
                        "maturity": json.loads(node["tech_maturity_mapping"]),
                    }

            for phase_name, phase in ai_research_task_phase_mapping.items():
                if phase["ai_methods_judgment"]["use_ai_methods"] == "yes":
                    ai_methods_scores = phase["ai_methods_judgment"]["ai_methods_scores"]
                    ai_methods_vectors_embeddings_result = llm_service.parse_embeddings(
                        texts=[x for x in ai_methods_scores.keys()],
                        dimensions=context.config["embedding_dimension"],
                        batch_size=10
                    )
                    if not ai_methods_vectors_embeddings_result.status:
                        logger.warning(f"ai_tech_id_to_info_mapping error, ai_methods_vectors_embeddings_result={ai_methods_vectors_embeddings_result.to_dict()}")
                        return self._default_output_result(idx, output_data)

                    ai_methods_vectors_embeddings = ai_methods_vectors_embeddings_result.get_data_on_results()
                    ai_tech_faiss_result = self.ai_tech_faiss_driver.search(ai_methods_vectors_embeddings, k=3)
                    ai_tech_faiss_result = [x[0] for x in ai_tech_faiss_result]

                    for i in range(len(ai_tech_faiss_result)):
                        ai_tech_faiss_result[i]["original_name"] = [x for x in ai_methods_scores.keys()][i]
                        ai_tech_faiss_result[i]["original_score"] = [x for x in ai_methods_scores.values()][i]

                    ai_tech_faiss_result = [
                        x for x in ai_tech_faiss_result if x["distance"] >= context.config["ai_tech_distance_threshold"]
                    ]

                    for item in ai_tech_faiss_result:
                        if item["id"] in ai_tech_id_to_info_mapping:
                            item.update(ai_tech_id_to_info_mapping[item["id"]])

                    for item in ai_tech_faiss_result:
                        publication_year_str = str(publication_year)
                        if publication_year_str in item["maturity"].keys():
                            item["maturity"] = item["maturity"][publication_year_str]
                        else:
                            item["maturity"] = 0

                    matched_ai_research_task_phase_mapping[phase_name]["ai_tech_db_matching"] = ai_tech_faiss_result
                else:
                    matched_ai_research_task_phase_mapping[phase_name]["ai_tech_db_matching"] = []

            for phase_name, phase in ai_research_task_phase_mapping.items():
                if phase["ai_methods_judgment"]["use_ai_methods"] != "yes":
                    history_methods_id_to_info_mapping = {}
                    for index in range(len(self.history_methods_db_df)):
                        item_id = self.history_methods_db_df.loc[index, "tools_methods_ids"][phase_name]
                        traditional_method = self.history_methods_db_df.loc[index, "tools_methods"][phase_name]
                        history_methods_id_to_info_mapping[item_id] = {"traditional_method": traditional_method}

                    traditional_methods_vectors_embeddings_result = llm_service.parse_embeddings(
                        texts=[phase["tools_methods"]],
                        dimensions=context.config["embedding_dimension"],
                        batch_size=10
                    )
                    if not traditional_methods_vectors_embeddings_result.status:
                        logger.warning(f"history_methods_id_to_info_mapping error, traditional_methods_vectors_embeddings_result={traditional_methods_vectors_embeddings_result.to_dict()}")
                        return self._default_output_result(idx, output_data)

                    traditional_methods_vectors_embeddings = traditional_methods_vectors_embeddings_result.get_data_on_results()
                    traditional_methods_faiss_result = self.history_methods_faiss_driver.search(traditional_methods_vectors_embeddings, k=3)
                    traditional_methods_faiss_result = [
                        x for x in traditional_methods_faiss_result if x[0]["distance"] >= context.config["history_methods_distance_threshold"]
                    ]
                    traditional_methods_faiss_id_list = [x[0]["id"] for x in traditional_methods_faiss_result]
                    traditional_methods_db_matching = [
                        history_methods_id_to_info_mapping[item_id]
                        for item_id in traditional_methods_faiss_id_list
                        if item_id in history_methods_id_to_info_mapping.keys()
                    ]
                    matched_ai_research_task_phase_mapping[phase_name]["traditional_methods_db_matching"] = traditional_methods_db_matching
                else:
                    matched_ai_research_task_phase_mapping[phase_name]["traditional_methods_db_matching"] = []

            output_data["matched_ai_research_task_phase_mapping"] = str(matched_ai_research_task_phase_mapping)

            if (
                isinstance(output_data["matched_ai_research_task_phase_mapping"], float)
                or isinstance(output_data["research_task_phase_mapping"], float)
                or isinstance(output_data["core_research_question_judgment"], float)
            ):
                logger.info(f"skip review paper, idx={idx}, paper_title={paper_title}")
                return self._default_output_result(idx, output_data)

            ai_replacement_judge_result = llm_service.parse_text(
                llm_name=context.config["llm_name"],
                llm_version=context.config["llm_version"],
                prompt_path="experiments/ai_exposure/llm/AIReplacementJudge/AIReplacementJudgePrompt.j2",
                format_check_path="experiments/ai_exposure/llm/AIReplacementJudge/AIReplacementJudgeFormatCheck.json",
                input_params={
                    "research_problem": output_data["core_research_question_judgment"],
                    "original_methodology": output_data["research_task_phase_mapping"],
                    "new_ai_methodology": output_data["matched_ai_research_task_phase_mapping"],
                },
                lang="en"
            )
            if not ai_replacement_judge_result.status:
                logger.warning(f"ai_replacement_judge_result error, idx={idx}, ai_replacement_judge_result={ai_replacement_judge_result.to_dict()}")
                return self._default_output_result(idx, output_data)

            ai_replacement_judge = ai_replacement_judge_result.get_data_on_results()
            output_data["replacement_judge"] = ai_replacement_judge.get("replacement_level", "")
            output_data["replacement_judge_reason"] = ai_replacement_judge.get("replacement_reason", "")

            total_score = sum([phase["ranking"] for phase in matched_ai_research_task_phase_mapping.values()])
            ai_exposure_rate = 0.0
            for phase in matched_ai_research_task_phase_mapping.values():
                if len(phase["ai_tech_db_matching"]) > 0:
                    ai_tech_db_matching_total_score = sum([float(x["original_score"]) for x in phase["ai_tech_db_matching"]])
                    ai_tech_db_matching_final_score = max([
                        x["maturity"] * x["original_score"] / ai_tech_db_matching_total_score
                        for x in phase["ai_tech_db_matching"]
                    ])
                    ai_exposure_rate += ai_tech_db_matching_final_score * float(phase["ranking"]) / float(total_score)

            output_data["ai_exposure_rate"] = ai_exposure_rate
            return self._default_output_result(idx, output_data)
        except Exception as e:
            logger.warning(f"phase three error, idx={idx}, e={e}")
            return self._default_output_result(idx, output_data)

    def flush_result(self, result, context):
        idx = result["idx"]
        normalized_output_data = self.normalize_output_data(
            result["output_data"],
            self.phase_three_output_columns(),
        )
        self.output_data_file_handler.save(normalized_output_data)
        logger.info(f"{idx} {result['output_data'].get('paper_title', 'unknown')} has been parsed successfully")

    def finalize(self, context):
        self.output_data_file_handler.save()
        logger.info("finished parsing papers phase three")
        logger.info("task finished!")

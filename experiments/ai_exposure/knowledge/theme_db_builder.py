import json

import pandas as pd
from docx import Document
from tqdm import tqdm
from infrastructure.llm.llm_api_prompt_parser import LLMAPIPromptParser
from infrastructure.logging.logger import get_logger
from infrastructure.storage.csv_file_handler import CSVFileHandler
from infrastructure.utils.path_utils import StrGenerator
from infrastructure.vector.faiss_vector_db_driver import FAISSVectorDBDriver

from experiments.ai_exposure.mappers.ai_exposure_mapper import AIExposureMapper


logger = get_logger(__name__)


class ThemeDBBuilder:
    @classmethod
    def create_committee_theme_knowledge(cls, task_id, committee_theme_xlsx_path):
        doc = Document(committee_theme_xlsx_path)
        total_text_list = []
        for para in doc.paragraphs:
            total_text_list.append(para.text)

        total_text_list = [x for x in total_text_list if x.strip(" ") != ""]
        domain_letter_list = ["A", "B", "C", "D", "E", "F", "G", "H", "T"]

        theme_col_dict = {
            "domain_name": [],
            "domain_id": [],
            "field_name": [],
            "field_id": [],
            "subfield_name": [],
            "subfield_id": []
        }
        letter_id = 0
        current_domain_name = ""
        current_domain_id = ""
        current_field_name = ""
        current_field_id = ""
        current_subfield_name = ""
        current_subfield_id = ""
        for text in total_text_list:
            unit_list = text.split(" ")

            unit_idx = 0
            for _ in range(100000):
                if unit_idx > len(unit_list) - 1:
                    break

                if domain_letter_list[letter_id] in unit_list[unit_idx]:
                    if len(unit_list[unit_idx]) == 2:
                        current_domain_name = unit_list[unit_idx + 1]
                        current_domain_id = unit_list[unit_idx]
                    elif len(unit_list[unit_idx]) == 3:
                        current_field_name = unit_list[unit_idx + 1]
                        current_field_id = unit_list[unit_idx]
                    elif len(unit_list[unit_idx]) == 5:
                        current_subfield_name = unit_list[unit_idx + 1]
                        current_subfield_id = unit_list[unit_idx]

                        theme_col_dict["domain_name"].append(current_domain_name)
                        theme_col_dict["domain_id"].append(current_domain_id.replace(".", ""))
                        theme_col_dict["field_name"].append(current_field_name)
                        theme_col_dict["field_id"].append(current_field_id)
                        theme_col_dict["subfield_name"].append(current_subfield_name)
                        theme_col_dict["subfield_id"].append(current_subfield_id)

                    unit_idx += 2
                else:
                    letter_id += 1
                    current_domain_name = ""
                    current_domain_id = ""
                    current_field_name = ""
                    current_field_id = ""
                    current_subfield_name = ""
                    current_subfield_id = ""

        theme_df = pd.DataFrame(theme_col_dict)
        for idx in tqdm(range(len(theme_df)), desc="creating committee theme knowledge ..."):
            AIExposureMapper.merge_committee_theme_chain({
                "task_id": task_id,
                "domain_name": theme_df.loc[idx, "domain_name"],
                "domain_id": theme_df.loc[idx, "domain_id"],
                "field_name": theme_df.loc[idx, "field_name"],
                "field_id": theme_df.loc[idx, "field_id"],
                "subfield_name": theme_df.loc[idx, "subfield_name"],
                "subfield_id": theme_df.loc[idx, "subfield_id"]
            })

    @classmethod
    def create_openalex_theme_knowledge(cls, task_id, openalex_theme_csv_path):
        theme_df = pd.read_excel(openalex_theme_csv_path, sheet_name=0)
        for idx in tqdm(range(len(theme_df)), desc="creating openalex theme knowledge ..."):
            AIExposureMapper.merge_openalex_theme_chain({
                "task_id": task_id,
                "domain_name": theme_df.loc[idx, "domain_name"],
                "domain_id": theme_df.loc[idx, "domain_id"],
                "field_name": theme_df.loc[idx, "field_name"],
                "field_id": theme_df.loc[idx, "field_id"],
                "subfield_name": theme_df.loc[idx, "subfield_name"],
                "subfield_id": theme_df.loc[idx, "subfield_id"],
                "topic_name": theme_df.loc[idx, "topic_name"],
                "topic_id": theme_df.loc[idx, "topic_id"],
                "topic_summary": theme_df.loc[idx, "summary"],
            })

            theme_name_list = [x.strip(" ") for x in theme_df.loc[idx, "keywords"].split(";") if x.strip(" ") != ""]
            for theme_name in theme_name_list:
                AIExposureMapper.merge_theme_node({
                    "topic_name": theme_df.loc[idx, "topic_name"],
                    "theme_name": theme_name,
                })

    @classmethod
    def create_ai_technology_theme_knowledge(
        cls,
        task_id,
        ai_technology_xlsx_path,
        llm_name,
        llm_version,
        ai_tech_vector_db_path,
        embedding_dimension,
        ai_tech_table_path,
        resume
    ):
        theme_df = pd.read_excel(ai_technology_xlsx_path, sheet_name=0)
        theme_df.columns = [str(col).strip() for col in theme_df.columns]
        result_dict = {}
        for idx in tqdm(range(len(theme_df)), desc="creating ai technology theme knowledge ..."):
            en_name = theme_df.iloc[idx, 0].lower()

            year_num_mapping = {}
            for col in theme_df.columns[1:]:
                year_num_mapping[str(col)] = int(theme_df.loc[idx, col])

            tech_maturity_values = [sum([x for x in year_num_mapping.values()][:i + 1]) for i in range(len(year_num_mapping))]
            tech_maturity_values = [x / max(tech_maturity_values) for x in tech_maturity_values]
            tech_maturity_mapping = dict(zip([k for k in year_num_mapping.keys()], tech_maturity_values))

            ai_tech_create_result = LLMAPIPromptParser.parse_text(
                llm_name=llm_name,
                llm_version=llm_version,
                prompt_path="experiments/ai_exposure/llm/AITechCreate/AITechCreatePrompt.j2",
                format_check_path="experiments/ai_exposure/llm/AITechCreate/AITechCreateFormatCheck.json",
                input_params={"en_name": en_name},
                lang="en"
            )
            if not ai_tech_create_result.status:
                logger.warning(f"ai_tech_create error, idx={idx}, ai_tech_create_result={ai_tech_create_result.to_dict()}")
                continue

            ai_tech_entity = ai_tech_create_result.get_data_on_results()
            result_dict[en_name] = {
                "id": StrGenerator.generate_uuid(),
                "en_name": en_name,
                "zh_name": ai_tech_entity["chinese_name"],
                "core_function": ai_tech_entity["core_function"],
                "research_application": ai_tech_entity["research_application"],
                "tech_maturity_mapping": tech_maturity_mapping
            }

        generate_domain_keywords_result = LLMAPIPromptParser.parse_text(
            llm_name=llm_name,
            llm_version=llm_version,
            prompt_path="experiments/ai_exposure/llm/GenerateDomainKeywords/GenerateDomainKeywordsPrompt.j2",
            format_check_path="experiments/ai_exposure/llm/GenerateDomainKeywords/GenerateDomainKeywordsFormatCheck.json",
            input_params={"domains": str([x for x in result_dict.keys()])},
            lang="en"
        )
        if not generate_domain_keywords_result.status:
            logger.warning(f"ai_tech_create error, generate_domain_keywords_result={generate_domain_keywords_result.to_dict()}")
            return

        domain_tech_list = generate_domain_keywords_result.get_data_on_results()["domains_keywords"]
        for domain_entity in domain_tech_list:
            domain_name = str(domain_entity.get("domain", "")).strip().lower()
            keyword_list = domain_entity.get("key_technical_keywords", [])
            if domain_name in result_dict.keys() and isinstance(keyword_list, list) and keyword_list:
                cleaned_keyword_list = [
                    str(keyword).strip()
                    for keyword in keyword_list
                    if str(keyword).strip()
                ]
                if cleaned_keyword_list:
                    result_dict[domain_name]["keyword_list"] = cleaned_keyword_list

        for domain_name, result in result_dict.items():
            if "keyword_list" not in result or not result["keyword_list"]:
                logger.warning(f"missing keyword_list for ai tech domain={domain_name}, fallback to domain name")
                result["keyword_list"] = [result["en_name"]]

        faiss_driver = FAISSVectorDBDriver(
            file_save_path=ai_tech_vector_db_path,
            dimension=embedding_dimension,
            index_type="flat_ip",
            resume=False
        )
        ai_tech_node_list = []
        for result in result_dict.values():
            keyword_id_list = [StrGenerator.generate_uuid() for _ in range(len(result["keyword_list"]))]
            tech_maturity_mapping = json.dumps(result["tech_maturity_mapping"], ensure_ascii=False)
            ai_tech_node = {
                "task_id": task_id,
                "en_name": result["en_name"],
                "zh_name": result["zh_name"],
                "tech_id": result["id"],
                "core_function": result["core_function"],
                "research_application": result["research_application"],
                "tech_maturity_mapping": tech_maturity_mapping,
                "keyword_list": result["keyword_list"],
                "keyword_id_list": keyword_id_list
            }
            AIExposureMapper.merge_ai_tech_node(ai_tech_node)
            ai_tech_node_list.append(ai_tech_node)

            parse_embeddings_result = LLMAPIPromptParser.parse_embeddings(
                texts=result["keyword_list"],
                dimensions=embedding_dimension,
                batch_size=10
            )
            if not parse_embeddings_result.status:
                logger.warning(f"ai_tech_create error, parse_embeddings_result={parse_embeddings_result.to_dict()}")
                return

            embedding_vectors_array = parse_embeddings_result.get_data_on_results()
            faiss_driver.insert(vectors=embedding_vectors_array, ids=keyword_id_list)

        faiss_driver.save()
        ai_tech_file_handler = CSVFileHandler(
            save_path=ai_tech_table_path,
            write_mode="w",
            resume=resume
        )
        ai_tech_file_handler.save(ai_tech_node_list)

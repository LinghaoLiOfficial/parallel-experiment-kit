import json
import re
from pathlib import Path

import numpy as np

from infrastructure.base.result import Result
from infrastructure.llm.llm_api_client import LLMAPIClient
from infrastructure.logging.logger import get_logger
from infrastructure.storage.json_file_handler import JsonFileHandler
from infrastructure.utils.json_validator import JsonValidator


logger = get_logger(__name__)


class LLMAPIPromptParser:
    @classmethod
    def parse_embeddings(cls, texts: list, dimensions: int, batch_size: int = 10, llm_extra_params=None, retry=5):
        llm_extra_params = llm_extra_params or {}
        output_embeddings_list = []
        texts_batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        for texts_batch in texts_batches:
            for _ in range(retry):
                try:
                    result = LLMAPIClient.output_embeddings(
                        texts=texts_batch,
                        dimensions=dimensions,
                        extra_params=llm_extra_params,
                    )
                    if not result.status:
                        logger.warning(f"output_embeddings func error, output_embeddings_result={result.to_dict()}")
                        continue
                    output_embeddings_list.append(result.get_data_on_results())
                    break
                except Exception as exc:
                    logger.error(f"LLMAPIPromptParser.parse_embeddings func error, e={exc}")
                    continue

        if not output_embeddings_list:
            return Result.build_error()
        return Result.build_success_with_results(np.concatenate(output_embeddings_list, axis=0))

    @classmethod
    def parse_text(
        cls,
        llm_name: str,
        llm_version: str,
        template_path: str,
        schemas_path: str,
        input_params: dict,
        to_json_format: bool = True,
        enable_thinking: bool = False,
        qa_mode: str = "one",
        lang: str = "zh",
        thinking_budget=None,
        llm_extra_params=None,
        retry=5,
    ):
        llm_extra_params = llm_extra_params or {}
        template_result = JsonFileHandler.read(template_path)
        if not template_result.status:
            return Result.build_error()

        generate_input_result = cls.generate_input(
            template=template_result.get_data_on_results(),
            params=input_params,
            qa_mode=qa_mode,
            lang=lang,
        )
        if not generate_input_result.status:
            return Result.build_error()

        llm_input = generate_input_result.get_data_on_results()
        llm_schemas = []
        if Path(schemas_path).exists():
            schemas_result = JsonFileHandler.read(schemas_path)
            if not schemas_result.status:
                return Result.build_error()
            llm_schemas = schemas_result.get_data_on_results()

        for _ in range(retry):
            try:
                output_text_result = LLMAPIClient.output_text(
                    llm_name=llm_name,
                    llm_version=llm_version,
                    messages=llm_input,
                    to_json_format=to_json_format,
                    enable_thinking=enable_thinking,
                    thinking_budget=thinking_budget,
                    extra_params=llm_extra_params,
                )
                if not output_text_result.status:
                    logger.warning(f"output_text func error, output_text_result={output_text_result.to_dict()}")
                    continue

                answer_content = output_text_result.get_data_on_results()["answer_content"]
                if not to_json_format:
                    return Result.build_success_with_results(answer_content)

                parse_result = cls.parse_str_to_json(answer_content)
                if not parse_result.status:
                    logger.warning(f"parse_str_to_json func error, parse_str_to_json_result={parse_result.to_dict()}")
                    continue

                json_data = parse_result.get_data_on_results()
                if llm_schemas:
                    check_result = JsonValidator.check_situations(data=json_data, schemas=llm_schemas)
                    if not check_result.status:
                        logger.warning(f"JsonValidator.check_situations func error, check_situations_result={check_result.to_dict()}")
                        continue

                return Result.build_success_with_results(json_data)
            except Exception as exc:
                logger.error(f"LLMAPIPromptParser.parse_text func error, e={exc}")
                continue

        return Result.build_error()

    @classmethod
    def generate_input(cls, template, params, qa_mode="one", lang="zh"):
        system_template = template["system_content"]
        user_template = template["user_content"]
        properties_layout_func = lambda properties: "\n" + "\n".join("\t" + f"{k}: {v}" for k, v in properties.items())
        bracket_layout_func = lambda x: f"({x})" if x else x

        words_dict = {
            "zh": {
                "you_are": "你是",
                "your_task_is_to": "你的任务是",
                "background_information": "背景信息",
                "input": "输入",
                "example_input": "示例输入",
                "example_output": "示例输出",
            },
            "en": {
                "you_are": "You are ",
                "your_task_is_to": "Your task is to ",
                "background_information": "Background Information",
                "input": "Input",
                "example_input": "Example Input",
                "example_output": "Example Output",
            },
        }[lang]

        if qa_mode != "one":
            return Result.build_error()

        if "role" in system_template:
            system_content = f'{words_dict["you_are"]}{system_template["role"]}. {words_dict["your_task_is_to"]}{system_template["task"]}'
        else:
            system_content = f'{words_dict["your_task_is_to"]}{system_template["task"]}'

        background_content = ""
        if "background" in user_template:
            if "properties" in user_template["background"]:
                background_content = (
                    f'{words_dict["background_information"]}{bracket_layout_func(user_template["background"]["object"])}: '
                    f'{properties_layout_func(user_template["background"]["properties"])}'
                )
            else:
                background_content = f'{words_dict["background_information"]}{bracket_layout_func(user_template["background"]["object"])}'

        input_content = ""
        if "input" in user_template:
            if "properties" in user_template["input"]:
                input_content = (
                    f'{words_dict["input"]}{bracket_layout_func(user_template["input"]["object"])}: '
                    f'{user_template["input"]["head"]} {properties_layout_func(user_template["input"]["properties"])}'
                )
            else:
                input_content = f'{words_dict["input"]}{bracket_layout_func(user_template["input"]["object"])}: {user_template["input"]["head"]}'

        descriptions_content = ""
        if "descriptions" in user_template:
            description_content_list = []
            for description in user_template["descriptions"]:
                description_content_list.append(f'{description["field"]}:')
                for sub_description in description["heads"]:
                    if "properties" in description:
                        description_content_list.append(f'{sub_description["head"]} {properties_layout_func(sub_description["properties"])}')
                    else:
                        description_content_list.append(f'{sub_description["head"]}')
            descriptions_content = "\n".join(description_content_list)

        examples_content = ""
        if "examples" in user_template:
            examples_content_list = []
            for i in range(len(user_template["examples"]["output"])):
                if len(user_template["examples"]["input"]) > 0:
                    examples_content_list.append(
                        f'{words_dict["example_input"]}[{i + 1}]{bracket_layout_func(user_template["examples"]["input"][i]["object"])}: '
                        f'{{{user_template["examples"]["input"][i]["properties"]}}}'
                    )
                examples_content_list.append(
                    f'{words_dict["example_output"]}[{i + 1}]{bracket_layout_func(user_template["examples"]["output"][i]["object"])}: '
                    f'{{{user_template["examples"]["output"][i]["properties"]}}}'
                )
            examples_content = "\n".join(examples_content_list)

        user_content = "\n".join([background_content, input_content, descriptions_content, examples_content])
        for param_k, param_v in params.items():
            user_content = user_content.replace(f"{{{param_k}}}", str(param_v))

        return Result.build_success_with_results(
            [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        )

    @classmethod
    def parse_str_to_json(cls, input_str):
        input_str = input_str.replace("true", "True").replace("false", "False")
        if "```json" in input_str:
            match = re.search(r"```json(.*?)```", input_str, re.DOTALL)
            output_str = match.group(1).strip() if match else ""
            try:
                return Result.build_success_with_results(json.loads(output_str))
            except Exception as exc:
                logger.error(f"generate error, e={exc}")
                return Result.build_error()

        try:
            return Result.build_success_with_results(json.loads(input_str))
        except Exception as exc:
            logger.error(f"generate error, e={exc}")
            return Result.build_error()

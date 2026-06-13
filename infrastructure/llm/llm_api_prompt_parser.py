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
        prompt_path: str,
        format_check_path: str,
        input_params: dict,
        to_json_format: bool = True,
        enable_thinking: bool = False,
        qa_mode: str = "one",
        lang: str = "en",
        thinking_budget=None,
        llm_extra_params=None,
        retry=5,
    ):
        llm_extra_params = llm_extra_params or {}
        prompt_result = JsonFileHandler.read(prompt_path)
        if not prompt_result.status:
            return Result.build_error()

        generate_input_result = cls.generate_input(
            template=prompt_result.get_data_on_results(),
            params=input_params,
            qa_mode=qa_mode,
        )
        if not generate_input_result.status:
            return Result.build_error()

        llm_input = generate_input_result.get_data_on_results()
        format_check = None
        if Path(format_check_path).exists():
            format_check_result = JsonFileHandler.read(format_check_path)
            if not format_check_result.status:
                return Result.build_error()
            format_check = format_check_result.get_data_on_results()

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
                if format_check is not None:
                    check_result = JsonValidator.check_allowed_output(data=json_data, format_check=format_check)
                    if not check_result.status:
                        logger.warning(
                            f"JsonValidator.check_allowed_output func error, "
                            f"check_allowed_output_result={check_result.to_dict()}"
                        )
                        continue

                return Result.build_success_with_results(json_data)
            except Exception as exc:
                logger.error(f"LLMAPIPromptParser.parse_text func error, e={exc}")
                continue

        return Result.build_error()

    @classmethod
    def generate_input(cls, template, params, qa_mode="one"):
        if qa_mode != "one":
            return Result.build_error()

        if not isinstance(template, str):
            return Result.build_error()

        rendered = template
        for param_k, param_v in params.items():
            rendered = rendered.replace(f"{{{{ {param_k} }}}}", str(param_v))
            rendered = rendered.replace(f"{{{{{param_k}}}}}", str(param_v))
        rendered = cls._strip_unreplaced_placeholders(rendered)

        system_content, user_content = cls._split_prompt(rendered)
        if not system_content or not user_content:
            return Result.build_error()

        return Result.build_success_with_results(
            [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        )

    @staticmethod
    def _strip_unreplaced_placeholders(text):
        return re.sub(r"\{\{\s*[\w\.]+\s*\}\}", "", text)

    @staticmethod
    def _split_prompt(text):
        system_match = re.search(r"===SYSTEM===\s*(.*?)\s*(?===USER===|$)", text, re.DOTALL)
        user_match = re.search(r"===USER===\s*(.*)$", text, re.DOTALL)
        system_content = system_match.group(1).strip() if system_match else ""
        user_content = user_match.group(1).strip() if user_match else ""
        return system_content, user_content

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

import json
import os

import numpy as np
from openai import OpenAI

from infrastructure.base.result import Result
from infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


class LLMAPIClient:
    models = {}

    @classmethod
    def _init_models(cls):
        if cls.models:
            return
        providers = {
            "qwen": (
                os.getenv("QWEN_TEXT_API_KEY") or os.getenv("QWEN_API_KEY"),
                os.getenv("QWEN_TEXT_API_URL") or os.getenv("QWEN_API_URL"),
            ),
            "qwen_embedding": (
                os.getenv("QWEN_EMBEDDING_API_KEY") or os.getenv("QWEN_API_KEY"),
                os.getenv("QWEN_EMBEDDING_API_URL") or os.getenv("QWEN_API_URL"),
            ),
            "zhipu": (os.getenv("ZHIPU_API_KEY"), os.getenv("ZHIPU_API_URL")),
            "openai": (os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_URL")),
        }
        for name, (api_key, base_url) in providers.items():
            if api_key and base_url:
                cls.models[name] = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"API LLM available, llms={list(cls.models.keys())}")

    @classmethod
    def output_text(
        cls,
        llm_name: str,
        llm_version: str,
        messages: list[dict],
        to_json_format=False,
        enable_thinking=False,
        thinking_budget=None,
        extra_params: dict | None = None,
    ):
        cls._init_models()
        extra_params = dict(extra_params or {})
        try:
            extra_params["stream"] = bool(enable_thinking)
            if llm_name == "qwen":
                if to_json_format:
                    extra_params["response_format"] = {"type": "json_object"}
                extra_body = {"enable_thinking": bool(enable_thinking)}
                if enable_thinking and thinking_budget is not None:
                    extra_body["thinking_budget"] = thinking_budget
                extra_params["extra_body"] = extra_body

            params = {"model": llm_version, "messages": messages}
            params.update(extra_params)
            completion = cls.models[llm_name].chat.completions.create(**params)

            if not enable_thinking:
                reasoning_content = ""
                answer_content = completion.choices[0].message.content
            else:
                reasoning_content = ""
                answer_content = ""
                for chunk in completion:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                        reasoning_content += delta.reasoning_content
                    if hasattr(delta, "content") and delta.content:
                        answer_content += delta.content
        except Exception as exc:
            logger.error(f"generate error, e={exc}")
            return Result.build_error()

        return Result.build_success_with_results(
            {"answer_content": answer_content, "reasoning_content": reasoning_content}
        )

    @classmethod
    def output_embeddings(cls, texts, dimensions: int = 1024, extra_params: dict | None = None):
        cls._init_models()
        if isinstance(texts, str):
            texts = [texts]
        params = {
            "model": "text-embedding-v4",
            "input": texts,
            "dimensions": dimensions,
        }
        params.update(extra_params or {})
        try:
            completion = cls.models["qwen_embedding"].embeddings.create(**params)
            result = json.loads(completion.model_dump_json())
            embeddings = [item["embedding"] for item in result["data"]]
            return Result.build_success_with_results(np.array(embeddings, dtype=np.float32))
        except Exception as exc:
            logger.error(f"embedding error, e={exc}")
            return Result.build_error()

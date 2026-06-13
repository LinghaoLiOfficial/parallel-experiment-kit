from infrastructure.llm.llm_api_prompt_parser import LLMAPIPromptParser


class LLMService:
    def parse_text(self, llm_name, llm_version, template_path, schemas_path, input_params, lang="en"):
        return LLMAPIPromptParser.parse_text(
            llm_name=llm_name,
            llm_version=llm_version,
            template_path=template_path,
            schemas_path=schemas_path,
            input_params=input_params,
            lang=lang
        )

    def parse_embeddings(self, texts, dimensions, batch_size=10):
        return LLMAPIPromptParser.parse_embeddings(
            texts=texts,
            dimensions=dimensions,
            batch_size=batch_size
        )

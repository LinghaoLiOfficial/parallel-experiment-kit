from infrastructure.llm.llm_api_prompt_parser import LLMAPIPromptParser


class ThemesJudgePromptParser:
    @classmethod
    def process(
            cls,
            paper_title,
            paper_abstract,
            candidate_theme_list,
            retry=5
    ):
        if not candidate_theme_list:
            return {}

        themes_judge_result = LLMAPIPromptParser.parse_text(
            llm_name="qwen",
            llm_version="qwen3-plus",
            prompt_path="experiments/ai_exposure/llm/ThemesJudgePromptParser/ThemesJudgePrompt.j2",
            format_check_path="experiments/ai_exposure/llm/ThemesJudgePromptParser/ThemesJudgePromptFormatCheck.json",
            input_params={
                "paper_title": paper_title,
                "paper_abstract": paper_abstract,
                "candidate_theme_list": candidate_theme_list,
            },
            lang="en",
            retry=retry,
        )
        if not themes_judge_result.status:
            return {}
        return themes_judge_result.get_data_on_results().get("themes_scores", {})

from infrastructure.llm.llm_api_client import LLMAPIClient
from infrastructure.llm.llm_api_prompt_parser import LLMAPIPromptParser

class ThemesJudgePromptParser:

    result_format_key = ["score", "reason"]

    @classmethod
    def generate(
            cls,
            paper_title,
            paper_abstract,
            candidate_theme_list
    ):
        system_content = "Your task is to assess the likelihood that the paper belongs to each candidate theme in the provided candidate theme list, using a Likert scale from 1 to 5 (where 1 means very unlikely and 5 means very likely), and provide a reason for each score."
        user_content = f"""
        Input:
            Paper Title: {paper_title}
            Paper Abstract: {paper_abstract}
            Candidate Theme List: {candidate_theme_list}  # Example: ['Artificial Intelligence', 'Biology', 'Physics']

        Instructions: 
            For each theme in the candidate theme list, analyze the paper and assign a score from 1 to 5 indicating the likelihood that the paper belongs to that theme. Provide a concise reason for each score. 
            Strictly return the result only in JSON format (without any other text).

        Example output (analysis result for illustrative candidate theme list):
            {{
                'Artificial Intelligence': {{'score': 4, 'reason': 'The paper focuses on neural networks and deep learning, which are key areas of AI.'}},
                'Biology': {{'score': 1, 'reason': 'No biological concepts or organisms are mentioned in the title or abstract.'}},
                'Physics': {{'score': 3, 'reason': 'The paper involves mathematical models but does not directly address core physics principles.'}}
            }}
        """

        template = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

        return template

    @classmethod
    def validate_en_format(cls, y, theme_list):
        for m, x in y.items():
            if m not in theme_list:
                return False

        return True

    @classmethod
    def process(
            cls,
            paper_title,
            paper_abstract,
            candidate_theme_list,
            retry=5
    ):
        themes_judge_template = cls.generate(
            paper_title=paper_title,
            paper_abstract=paper_abstract,
            candidate_theme_list=candidate_theme_list
        )

        for _ in range(retry):
            try:
                themes_judge_result = LLMAPIClient.output_text(
                    llm_name="qwen",
                    llm_version="qwen3-plus",
                    messages=themes_judge_template,
                    to_json_format=True,
                )
                if not themes_judge_result.status:
                    continue
                parse_result = LLMAPIPromptParser.parse_str_to_json(
                    themes_judge_result.get_data_on_results()["answer_content"]
                )
                if parse_result.status and cls.validate_en_format(parse_result.get_data_on_results(), candidate_theme_list):
                    return parse_result.get_data_on_results()
            except Exception as e:
                print(e)

        return {}

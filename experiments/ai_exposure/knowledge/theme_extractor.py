from experiments.ai_exposure.llm.ThemesJudgePromptParser import ThemesJudgePromptParser
from experiments.ai_exposure.mappers.ai_exposure_mapper import AIExposureMapper


class ThemeExtractor:
    node_info_list = [
        {"type": "task", "property": "task_id"},
        {"type": "domain", "property": "name"},
        {"type": "field", "property": "name"},
        {"type": "subfield", "property": "name"},
        {"type": "topic", "property": "name"},
        {"type": "theme", "property": "name"},
    ]

    def __init__(self):
        self.theme_result = {
            "domain": [],
            "field": [],
            "subfield": [],
            "topic": [],
            "theme": []
        }

    def recursion_fetch_and_rank(
        self,
        node_idx,
        value,
        paper_title,
        paper_abstract,
        ahead_level,
        belong
    ):
        neo4j_result = AIExposureMapper.match_next_nodes(
            node_type=self.node_info_list[node_idx]["type"],
            node_property=self.node_info_list[node_idx]["property"],
            next_node_type=self.node_info_list[node_idx + 1]["type"],
            params={
                self.node_info_list[node_idx]["property"]: value,
                "belong": belong
            }
        )
        candidate_theme_list = []
        if neo4j_result.verify_data_on_results():
            candidate_theme_list = [x["m"]["name"] for x in neo4j_result.get_data_on_results()]
        candidate_theme_list = list(set(candidate_theme_list))

        themes_judge_result = ThemesJudgePromptParser.process(
            paper_title=paper_title,
            paper_abstract=paper_abstract,
            candidate_theme_list=candidate_theme_list
        )

        avg_score = sum([x["score"] for x in themes_judge_result.values()]) / len(themes_judge_result)
        chosen_theme_list = {k: v for k, v in themes_judge_result.items() if v["score"] >= avg_score and v["score"] >= 5}
        self.theme_result[self.node_info_list[node_idx + 1]["type"]] += [f"{k}:{v['score']}" for k, v in chosen_theme_list.items()]
        if node_idx + 1 != len(self.node_info_list) - ahead_level:
            for theme_name in chosen_theme_list:
                self.recursion_fetch_and_rank(
                    node_idx=node_idx + 1,
                    value=theme_name,
                    paper_title=paper_title,
                    paper_abstract=paper_abstract,
                    ahead_level=ahead_level,
                    belong=belong
                )

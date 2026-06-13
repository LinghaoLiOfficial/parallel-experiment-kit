PHASE_ONE_BASE_COLUMNS = [
    "paper_title",
    "paper_abstract",
    "publication_year",
    "review_paper_judgment",
    "review_paper_reason",
    "openalex_theme_classification",
    "committee_theme_classification",
    "macro_paradigm_judgment",
    "macro_paradigm_reason",
    "core_research_question_judgment",
    "core_research_question_reason",
    "core_research_question_energy_transition_related",
    "core_research_question_climate_change_related",
    "research_task_phase_mapping",
    "use_ai_phases",
]

PHASE_TWO_AI_COLUMNS = [
    "ai_usage_rate",
    "ai_irreplaceable_score",
    "fully_based_on_ai",
    "partially_based_on_ai",
    "ai_necessity",
    "ai_necessity_reason",
    "ai_usage_level",
    "ai_usage_level_reason",
]

PHASE_THREE_COLUMNS = [
    "ai_research_task_phase_mapping_result",
    "ai_research_use_ai_phases",
    "matched_ai_research_task_phase_mapping",
    "replacement_judge",
    "replacement_judge_reason",
    "ai_exposure_rate",
]


def phase_one_output_columns():
    return list(PHASE_ONE_BASE_COLUMNS)


def phase_two_output_columns():
    return phase_one_output_columns() + list(PHASE_TWO_AI_COLUMNS)


def phase_three_output_columns():
    return phase_two_output_columns() + list(PHASE_THREE_COLUMNS)

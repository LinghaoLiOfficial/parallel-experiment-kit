from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from experiments.ai_exposure.schema import (
    phase_one_output_columns,
    phase_three_output_columns,
    phase_two_output_columns,
)


STAGE_TO_COLUMNS = {
    "phase_one": phase_one_output_columns(),
    "phase_two": phase_two_output_columns(),
    "phase_three": phase_three_output_columns(),
}


def fix_csv_schema(input_path: Path, output_path: Path, stage: str) -> None:
    df = pd.read_csv(input_path, encoding="utf-8")
    expected_columns = STAGE_TO_COLUMNS[stage]

    existing_columns = list(df.columns)
    ordered_columns = [column for column in expected_columns if column in existing_columns]
    remaining_columns = [column for column in existing_columns if column not in ordered_columns]
    final_columns = ordered_columns + remaining_columns

    fixed_df = df.reindex(columns=final_columns)
    fixed_df.to_csv(output_path, index=False, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reorder AI exposure CSV columns to the fixed stage schema.")
    parser.add_argument("input_path", type=Path, help="Input CSV path.")
    parser.add_argument("output_path", type=Path, help="Output CSV path.")
    parser.add_argument(
        "--stage",
        choices=sorted(STAGE_TO_COLUMNS.keys()),
        required=True,
        help="Stage schema to apply.",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    fix_csv_schema(args.input_path, args.output_path, args.stage)

#!/usr/bin/env python3

import argparse
import pandas as pd
from pathlib import Path

SAILOR_COLUMNS = [
    "CompetitorID", 
    "Class",
    "Sail No",
    "Helm Name",
    "Crew Name",
]

def choose_value(corrected, raw):

    if pd.notna(corrected):

        corrected = str(corrected).strip()

        if corrected != "":
            return corrected

    return raw

def update_sailors_reference(
    validation_df,
    sailors_csv,
):
    sailors_df = pd.read_csv(
        sailors_csv,
        dtype=str,
        usecols=SAILOR_COLUMNS,
    )

    # Clean the existing IDs and sail numbers.
    sailors_df["CompetitorID"] = (
        sailors_df["CompetitorID"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    sailors_df["Sail No"] = (
        sailors_df["Sail No"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    update_rows = validation_df[
        validation_df["status"]
        .astype(str)
        .str.strip()
        .str.upper()
        == "UPDATE_SAILOR"
    ]

    if len(update_rows) == 0:
        return

    def next_competitor_id():
        numbers = []

        for competitor_id in sailors_df["CompetitorID"]:
            competitor_id = str(competitor_id).strip().upper()

            if competitor_id.startswith("WFSC"):
                number_part = competitor_id[4:]

                if number_part.isdigit():
                    numbers.append(int(number_part))

        next_number = max(numbers, default=0) + 1

        return f"WFSC{next_number:04d}"

    for _, row in update_rows.iterrows():

        # Manual-entry validation workbook
        if not has_ocr_columns(validation_df):
            competitor_id = str(
                row.get("competitor_id", "")
            ).strip()

            sail_number = str(
                row.get("sail_number", "")
            ).strip()

            sailor_values = {
                "Class": row.get("boat_type", ""),
                "Sail No": sail_number,
                "Helm Name": row.get("helm", ""),
                "Crew Name": row.get("crew", ""),
            }

        # OCR validation workbook
        else:
            competitor_id = str(
                row.get("competitor_id", "")
            ).strip()

            sail_number = choose_value(
                row.get("corrected_sail_number", ""),
                row.get("raw_sail_number", ""),
            )

            sail_number = str(sail_number).strip()

            sailor_values = {
                "Class": choose_value(
                    row.get("corrected_class", ""),
                    row.get("raw_boat_type", ""),
                ),
                "Sail No": sail_number,
                "Helm Name": choose_value(
                    row.get("corrected_helm", ""),
                    row.get("raw_helm", ""),
                ),
                "Crew Name": choose_value(
                    row.get("corrected_crew", ""),
                    row.get("raw_crew", ""),
                ),
            }

        # If the validation workbook has no CompetitorID,
        # try to recover it using the sail number.
        if competitor_id == "" or competitor_id.lower() == "nan":
            existing_match = sailors_df[
                sailors_df["Sail No"] == sail_number
            ]

            if len(existing_match) >= 1:
                competitor_id = (
                    existing_match
                    .iloc[0]["CompetitorID"]
                )
            else:
                competitor_id = next_competitor_id()

        sailor_values["CompetitorID"] = competitor_id

        # Update the existing competitor if the ID is known.
        id_match = (
            sailors_df["CompetitorID"]
            == competitor_id
        )

        if id_match.any():
            for column, value in sailor_values.items():
                sailors_df.loc[
                    id_match,
                    column,
                ] = value

        # Otherwise append a genuinely new competitor.
        else:
            new_df = pd.DataFrame(
                [sailor_values],
                columns=SAILOR_COLUMNS,
            )

            sailors_df = pd.concat(
                [
                    sailors_df,
                    new_df,
                ],
                ignore_index=True,
            )

    sailors_df = sailors_df.drop_duplicates(
        subset=["CompetitorID"],
        keep="last",
    )

    backup_file = (
        Path(sailors_csv)
        .with_suffix(".bak.csv")
    )

    sailors_df.to_csv(
        backup_file,
        index=False,
        columns=SAILOR_COLUMNS,
    )

    sailors_df.to_csv(
        sailors_csv,
        index=False,
        columns=SAILOR_COLUMNS,
    )

    print(
        f"Updated {sailors_csv}"
    )


    if len(new_rows) > 0:

        new_df = pd.DataFrame(
            new_rows,
            columns=SAILOR_COLUMNS,
        )

        print("\n===== NEW SAILOR ROWS =====\n")
        
        print(new_df)

        sailors_df = pd.concat(
            [
                sailors_df,
                new_df,
            ],
            ignore_index=True,
        )

        sailors_df = sailors_df.drop_duplicates(
            subset=["Sail No"],
            keep="last",
        )

        backup_file = (
            Path(sailors_csv)
            .with_suffix(".bak.csv")
        )
        
        sailors_df.to_csv(
            backup_file,
            index=False,
            columns=SAILOR_COLUMNS,
        )

        print(
            f"Updated {sailors_csv}"
        )

def has_ocr_columns(df):

    return all(
        col in df.columns
        for col in [
            "corrected_class",
            "corrected_sail_number",
            "corrected_helm",
            "corrected_crew",
        ]
    )


def build_race_workbook(
    validation_df,
):
    # Manual-entry workbook
    if not has_ocr_columns(
        validation_df
    ):
        return validation_df[
            [
                "competitor_id",
                "boat_type",
                "sail_number",
                "helm",
                "crew",
                "elapsed_time",
                "total_laps",
                "status",
            ]
        ].copy()

    # OCR workbook
    race_df = pd.DataFrame()

    if "competitor_id" in validation_df.columns:
        race_df["competitor_id"] = (
            validation_df["competitor_id"]
        )
    else:
        race_df["competitor_id"] = ""

    race_df["boat_type"] = validation_df.apply(
        lambda row: choose_value(
            row.get("corrected_class", ""),
            row.get("raw_boat_type", ""),
        ),
        axis=1,
    )

    race_df["sail_number"] = validation_df.apply(
        lambda row: choose_value(
            row.get("corrected_sail_number", ""),
            row.get("raw_sail_number", ""),
        ),
        axis=1,
    )

    race_df["helm"] = validation_df.apply(
        lambda row: choose_value(
            row.get("corrected_helm", ""),
            row.get("raw_helm", ""),
        ),
        axis=1,
    )

    race_df["crew"] = validation_df.apply(
        lambda row: choose_value(
            row.get("corrected_crew", ""),
            row.get("raw_crew", ""),
        ),
        axis=1,
    )

    race_df["elapsed_time"] = (
        validation_df["elapsed_time"]
    )

    race_df["total_laps"] = (
        validation_df["total_laps"]
    )

    race_df["status"] = (
        validation_df["status"]
    )

    return race_df


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validation",
        required=True,
    )

    parser.add_argument(
        "--sailors",
        required=True,
    )

    parser.add_argument(
        "--output",
        default="race1_generated.xlsx",
    )

    args = parser.parse_args()

    validation_df = pd.read_excel(
        args.validation,
    )

    update_sailors_reference(
        validation_df,
        args.sailors,
    )

    race_df = build_race_workbook(
        validation_df,
    )

    race_df.to_excel(
        args.output,
        index=False,
    )

    print(
        f"Created {args.output}"
    )

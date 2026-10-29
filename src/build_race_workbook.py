#!/usr/bin/env python3

import argparse
import pandas as pd
from pathlib import Path

SAILOR_COLUMNS = [
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
        usecols=[0, 1, 2, 3],
    )

    sailors_df.columns = SAILOR_COLUMNS

    new_rows = []

    update_rows = validation_df[
        validation_df["status"]
        == "UPDATE_SAILOR"
    ]

    if len(update_rows) == 0:

        return


    for _, row in update_rows.iterrows():
    
        #
        # Manual-entry workbook
        #
    
        if not has_ocr_columns(
            validation_df
        ):
    
            new_rows.append(
                {
                    "Class":
                        row["boat_type"],
    
                    "Sail No":
                        row["sail_number"],
    
                    "Helm Name":
                        row["helm"],
    
                    "Crew Name":
                        row["crew"],
                }
            )
    
        #
        # OCR workbook
        #
    
        else:
    
            new_rows.append(
                {
                    "Class":
                        choose_value(
                            row["corrected_class"],
                            row["raw_boat_type"],
                        ),
    
                    "Sail No":
                        choose_value(
                            row["corrected_sail_number"],
                            row["raw_sail_number"],
                        ),
    
                    "Helm Name":
                        choose_value(
                            row["corrected_helm"],
                            row["raw_helm"],
                        ),
    
                    "Crew Name":
                        choose_value(
                            row["corrected_crew"],
                            row["raw_crew"],
                        ),
                }
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

        sailors_df.to_csv(
            sailors_csv,
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

    #
    # Manual entry workbook
    #

    if not has_ocr_columns(
        validation_df
    ):

        return validation_df[
            [
                "boat_type",
                "sail_number",
                "helm",
                "crew",
                "elapsed_time",
                "total_laps",
            ]
        ].copy()

    #
    # OCR workbook
    #

    race_df = pd.DataFrame()


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

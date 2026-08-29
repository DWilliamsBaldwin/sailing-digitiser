#!/usr/bin/env python3

import argparse
import pandas as pd
from pathlib import Path

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
    )

    new_rows = []

    update_rows = validation_df[
        validation_df["status"]
        == "UPDATE_SAILOR"
    ]

    for _, row in update_rows.iterrows():

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
            new_rows
        )

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

        sailors_df.to_csv(
            sailors_csv,
            index=False,
        )

        print(
            f"Updated {sailors_csv}"
        )

def build_race_workbook(
    validation_df,
):

    race_df = pd.DataFrame()

    race_df["boat_type"] = (
        validation_df.apply(
            lambda r: choose_value(
                r["corrected_class"],
                r["raw_boat_type"],
            ),
            axis=1,
        )
    )

    race_df["sail_number"] = (
        validation_df.apply(
            lambda r: choose_value(
                r["corrected_sail_number"],
                r["raw_sail_number"],
            ),
            axis=1,
        )
    )

    race_df["helm"] = (
        validation_df.apply(
            lambda r: choose_value(
                r["corrected_helm"],
                r["raw_helm"],
            ),
            axis=1,
        )
    )

    race_df["crew"] = (
        validation_df.apply(
            lambda r: choose_value(
                r["corrected_crew"],
                r["raw_crew"],
            ),
            axis=1,
        )
    )

    race_df["elapsed_time"] = (
        validation_df["elapsed_time"]
    )

    race_df["total_laps"] = (
        validation_df["total_laps"]
    )

    race_df["review_status"] = (
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

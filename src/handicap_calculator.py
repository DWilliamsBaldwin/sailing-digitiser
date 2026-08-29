import pandas as pd


def calculate_handicap(
    race_excel_path,
    py_csv_path,
    output_path=None,
):

    # Read race workbook

    df = pd.read_excel(
        race_excel_path,
        engine="openpyxl",
    )

    # Read PY lookup

    py_df = pd.read_csv(
        py_csv_path
    )

    # Make boat type matching case-insensitive

    df["boat_type"] = (
        df["boat_type"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    py_df["boat_type"] = (
        py_df["boat_type"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Split finishers and non-finishers

    special_statuses = [
        "DNF",
        "DNS",
        "RET",
    ]

    finished_df = df[
        ~df["elapsed_time"]
        .astype(str)
        .str.upper()
        .isin(special_statuses)
    ].copy()

    non_finishers_df = df[
        df["elapsed_time"]
        .astype(str)
        .str.upper()
        .isin(special_statuses)
    ].copy()

    competitor_count = len(df)

    #
    # FINISHERS
    #

    finished_df["elapsed_time"] = pd.to_timedelta(
        "00:"
        + finished_df["elapsed_time"].astype(str)
    )

    max_laps = (
        finished_df["total_laps"]
        .max()
    )

    finished_df["average_lap_time"] = (
        finished_df["elapsed_time"]
        /
        finished_df["total_laps"]
    )

    finished_df["adjusted_elapsed_time"] = (
        finished_df["average_lap_time"]
        *
        max_laps
    )

    mask_max = (
        finished_df["total_laps"]
        ==
        max_laps
    )

    finished_df.loc[
        mask_max,
        "adjusted_elapsed_time"
    ] = finished_df.loc[
        mask_max,
        "elapsed_time"
    ]

    finished_df = finished_df.merge(
        py_df,
        on="boat_type",
        how="left",
    )

    finished_df["corrected_time"] = (
        finished_df["adjusted_elapsed_time"]
        *
        1000
        /
        finished_df["py"]
    )

    finished_df["corrected_position"] = (
        finished_df["corrected_time"]
        .rank(
            method="min",
            ascending=True,
        )
        .astype("Int64")
    )

    #
    # NON FINISHERS
    #

    penalty_score = (
        competitor_count
        + 1
    )

    if len(non_finishers_df) > 0:

        non_finishers_df["average_lap_time"] = pd.NaT

        non_finishers_df[
            "adjusted_elapsed_time"
        ] = pd.NaT

        non_finishers_df["py"] = pd.NA

        non_finishers_df[
            "corrected_time"
        ] = pd.NaT

        non_finishers_df[
            "corrected_position"
        ] = penalty_score

    #
    # COMBINE RESULTS
    #

    results_df = pd.concat(
        [
            finished_df,
            non_finishers_df,
        ],
        ignore_index=True,
    )

    #
    # HUMAN-READABLE TIMES
    #

    results_df["elapsed_time_hms"] = (
        results_df["elapsed_time"]
        .astype(str)
    )

    results_df["corrected_time_hms"] = (
        results_df["corrected_time"]
        .astype(str)
    )

    #
    # SORT RESULTS
    #

    results_df.sort_values(
        "corrected_position",
        inplace=True,
    )

    results_df.reset_index(
        drop=True,
        inplace=True,
    )

    #
    # WRITE OUTPUT
    #

    if output_path:

        if output_path.lower().endswith(
            ".xlsx"
        ):

            results_df.to_excel(
                output_path,
                index=False,
            )

        else:

            results_df.to_csv(
                output_path,
                index=False,
            )

    return results_df



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Calculate handicap corrected times for a race sheet.')
    parser.add_argument('--race', default='race1.xlsx', help='Path to race workbook (Excel file).')
    parser.add_argument('--py', default='py_lookup.csv', help='Path to PY lookup CSV file.')
    parser.add_argument('--output', default='race1_results.xlsx', help='Output file path (Excel or CSV).')
    args = parser.parse_args()
    results = calculate_handicap(args.race, args.py, args.output)
    results.reset_index(drop=True,inplace=True)
    results.index = results.index + 1

    # Print out key fields for verification

    print(results[['boat_type','sail_number','helm','crew','elapsed_time','total_laps','py','corrected_time','corrected_position']])

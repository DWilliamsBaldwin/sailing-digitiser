import pandas as pd
import webbrowser
from pathlib import Path

def load_race_results(path, race_number):
    """
    Load a single race results workbook and rename the
    corrected_position column.
    """

    df = pd.read_excel(path)

    keep_cols = [
        "boat_type",
        "sail_number",
        "helm",
        "crew",
        "corrected_position",
    ]

    df = df[keep_cols].copy()

    df.rename(
        columns={
            "corrected_position":
            f"race_{race_number}_pos"
        },
        inplace=True,
    )

    return df


def merge_races(race1, race2, race3):

    merged = race1.merge(
        race2,
        on="sail_number",
        how="outer",
        suffixes=("_r1", "_r2"),
    )

    merged = merged.merge(
        race3,
        on="sail_number",
        how="outer",
    )

    return merged


def apply_dnc_scores(df):

    fleet_size = len(df)

    dnc_score = fleet_size + 1

    for col in [
        "race_1_pos",
        "race_2_pos",
        "race_3_pos",
    ]:

        df[col] = (
            df[col]
            .fillna(dnc_score)
            .astype(int)
        )

    return df, dnc_score


def calculate_scores(df):

    race_cols = [
        "race_1_pos",
        "race_2_pos",
        "race_3_pos",
    ]

    df["gross_score"] = df[race_cols].sum(axis=1)

    df["discard"] = df[race_cols].max(axis=1)

    df["nett_score"] = (
        df["gross_score"]
        - df["discard"]
    )

    return df


def countback_key(row):

    scores = sorted([
        row["race_1_pos"],
        row["race_2_pos"],
        row["race_3_pos"],
    ])

    return tuple(scores)


def assign_final_positions(df):

    df = df.sort_values(
        by=["nett_score"],
        ascending=True,
    )

    df["_countback"] = (
        df.apply(
            countback_key,
            axis=1,
        )
    )

    df = df.sort_values(
        by=[
            "nett_score",
            "_countback",
        ]
    )

    df["final_pos"] = (
        range(
            1,
            len(df) + 1
        )
    )

    df.drop(
        columns=["_countback"],
        inplace=True,
    )

    return df


def validate_competitors(df):

    warnings = []

    grouped = df.groupby(
        "sail_number"
    )

    for sail_no, group in grouped:

        helms = (
            group["helm"]
            .dropna()
            .unique()
        )

        if len(helms) > 1:

            warnings.append(
                {
                    "sail_number":
                    sail_no,

                    "issue_type":
                    "HELM_MISMATCH",

                    "message":
                    ", ".join(helms),
                }
            )

    return pd.DataFrame(
        warnings
    )


def create_display_table(df, dnc_score):

    display = pd.DataFrame()

    display["Position"] = df["final_pos"]

    display["Boat"] = (
        df["boat_type_r1"]
        .combine_first(df["boat_type_r2"])
        .combine_first(df["boat_type"])
    )

    display["Sail Number"] = df["sail_number"]

    display["Helm"] = (
        df["helm_r1"]
        .combine_first(df["helm_r2"])
        .combine_first(df["helm"])
    )

    display["Crew"] = (
        df["crew_r1"]
        .combine_first(df["crew_r2"])
        .combine_first(df["crew"])
        .fillna("")
    )

    race_cols = [
        "race_1_pos",
        "race_2_pos",
        "race_3_pos",
    ]

    for race_col in race_cols:
    
        display_col = []
    
        race_index = race_cols.index(race_col)
    
        for idx, row in df.iterrows():
    
            race_scores = [
                row["race_1_pos"],
                row["race_2_pos"],
                row["race_3_pos"],
            ]
    
            discard_index = race_scores.index(
                max(race_scores)
            )
    
            score = int(row[race_col])
    
            text = str(score)
    
            if score == dnc_score:
                text = f"{score} DNC"
    
            if race_index == discard_index:
                text = f"({text})"
    
            display_col.append(text)
    
        display[race_col] = display_col

    display["Total Score"] = df["gross_score"]
    display["Nett Score"] = df["nett_score"]

    for col in [
        "race_1_pos",
        "race_2_pos",
        "race_3_pos",
    ]:

        display[col] = (
            display[col]
            .apply(style_race_result)
        )

    return display

def style_race_result(value):

    value_str = str(value).strip()

    if value_str in ["1", "(1)"]:
        return f'<span class="gold">{value_str}</span>'

    if value_str in ["2", "(2)"]:
        return f'<span class="silver">{value_str}</span>'

    if value_str in ["3", "(3)"]:
        return f'<span class="bronze">{value_str}</span>'

    return value_str



if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Series scorer for sailing events"
    )

    parser.add_argument(
        "--race1",
        required=True,
        help="Path to Race 1 results workbook"
    )

    parser.add_argument(
        "--race2",
        required=True,
        help="Path to Race 2 results workbook"
    )

    parser.add_argument(
        "--race3",
        required=True,
        help="Path to Race 3 results workbook"
    )

    parser.add_argument(
        "--output",
        default="final_standings.xlsx",
        help="Output standings workbook"
    )

    args = parser.parse_args()

    race1 = load_race_results(
        args.race1,
        1,
    )

    race2 = load_race_results(
        args.race2,
        2,
    )

    race3 = load_race_results(
        args.race3,
        3,
    )

    standings = merge_races(
        race1,
        race2,
        race3,
    )

    standings, dnc_score = (
        apply_dnc_scores(
            standings
        )
    )

    standings = (
        calculate_scores(
            standings
        )
    )

    standings = (
        assign_final_positions(
            standings
        )
    )

    standings.to_excel(
        args.output,
        index=False,
    )

    print(
        f"Created {args.output}"
    )

    display_table = create_display_table(
        standings,
        dnc_score,
    )

    html_file = "final_standings.html"
    
    table_html = display_table.to_html(
        index=False,
        escape=False
    )
    
    html = f"""
    <html>
    
    <head>
    
    <style>
    
    body {{
        font-family: Arial, sans-serif;
        margin: 20px;
    }}
    
    table {{
        border-collapse: collapse;
    }}
    
    th {{
        background-color: #e6e6e6;
        padding: 8px;
        border: 1px solid black;
    }}
    
    td {{
        padding: 6px;
        border: 1px solid black;
    }}
    
    .gold {{
        display: block;
        background-color: #FFD700;
        font-weight: bold;
        text-align: center;
        width: 100%;
        height: 100%;
        padding: 4px;
        box-sizing: border-box;
    }}

    
    .silver {{
        display: block;
        background-color: #C0C0C0;
        font-weight: bold;
        text-align: center;
        width: 100%;
        height: 100%;
        padding: 4px;
        box-sizing: border-box;
    }}

    
    .bronze {{
        display: block;
        background-color: #CD7F32;
        color: white;
        font-weight: bold;
        text-align: center;
        width: 100%;
        height: 100%;
        padding: 4px;
        box-sizing: border-box;
    }}

    td {{
        padding: 6px;
        border: 1px solid black;
        text-align: center;
    }}

    </style>
    
    </head>
    
    <body>
    
    <h1>Trophy Day Standings</h1>
    
    {table_html}
    
    </body>
    
    </html>
    """
    
    with open(html_file, "w") as f:
        f.write(html)
    
    webbrowser.open(
        Path(html_file).resolve().as_uri()
    )



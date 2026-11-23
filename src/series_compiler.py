from pathlib import Path
from datetime import datetime
import pandas as pd
import webbrowser
import base64


from series_scorer import (
    load_race_results,
    apply_dnc_scores,
    assign_final_positions,
    validate_competitors,
    create_display_table,
)

RESULTS_DIR = Path("results")

def discover_series_files(
    race_type,
    start_date,
    end_date,
):
    files = []

    for path in RESULTS_DIR.glob("*_results.xlsx"):

        parts = path.stem.split("_")

        if len(parts) < 4:
            continue

        file_race_type = parts[1]

        if file_race_type != race_type:
            continue

        date_string = parts[2]

        race_date = datetime.strptime(
            date_string,
            "%d%m%Y"
        ).date()

        if (
            start_date
            <= race_date
            <= end_date
        ):
            files.append(
                (
                    race_date,
                    path
                )
            )

    files.sort()

    return [x[1] for x in files]

def load_all_races(
    race_files,
):
    races = []

    for i, path in enumerate(
        race_files,
        start=1,
    ):
        races.append(
            load_race_results(
                path,
                i
            )
        )

    return races

def merge_n_races(
    race_list
):
    merged = race_list[0]

    for race_df in race_list[1:]:

        merged = merged.merge(
            race_df,
            on="competitor_id",
            how="outer"
        )

    return merged

def get_discard_count(
    race_count
):
    return race_count // 3

def compile_series():

    print(
        "\n====================================="
    )
    print(
        "      Compile New Series"
    )
    print(
        "====================================="
    )

    series_name = input(
        "\nSeries name: "
    ).strip()

    print(
        "\nRace type:"
    )
    print(
        "1 - Handicap"
    )
    print(
        "2 - Pursuit"
    )

    race_choice = input(
        "\nSelect race type: "
    ).strip()

    if race_choice == "1":

        race_type = "HAND"

    elif race_choice == "2":

        race_type = "PURS"

    else:

        print(
            "\nInvalid race type."
        )

        return

    print(
        "\nScoring mode:"
    )
    print(
        "1 - By boat"
    )
    print(
        "2 - By sailor"
    )

    scoring_choice = input(
        "\nSelect scoring mode: "
    ).strip()

    if scoring_choice == "2":

        print(
            "\nBy sailor scoring "
            "does not currently work."
        )

        return

    if scoring_choice != "1":

        print(
            "\nInvalid scoring mode."
        )

        return

    start_date = datetime.strptime(
        input(
            "\nStart date "
            "(DD/MM/YYYY): "
        ),
        "%d/%m/%Y"
    ).date()

    end_date = datetime.strptime(
        input(
            "End date "
            "(DD/MM/YYYY): "
        ),
        "%d/%m/%Y"
    ).date()

    race_files = discover_series_files(
        race_type,
        start_date,
        end_date,
    )

    if len(race_files) == 0:
    
        print(
            "\nNo matching race files found."
        )
    
        return

    print(
        "\nMatching files:"
    )

    for path in race_files:

        print(
            f"  {path.name}"
        )

    standard_discards = (
        get_discard_count(
            len(race_files)
        )
    )

    use_standard = input(
        "\nUse standard discard profile "
        f"({standard_discards})? "
        "(Y/N): "
    ).upper()

    if use_standard in [
        "Y",
        "YES",
    ]:

        discards = (
            standard_discards
        )

    else:

        discards = int(
            input(
                "Number of discards: "
            )
        )

    print(
        "\nSeries Summary"
    )

    print(
        f"Series: {series_name}"
    )

    print(
        f"Race type: {race_type}"
    )

    print(
        f"Files found: "
        f"{len(race_files)}"
    )

    print(
        f"Discards: "
        f"{discards}"
    )

    print(
        "\nLoading race workbooks..."
    )
    
    if discards >= len(race_files):
    
        print(
            "\nToo many discards "
            "for the number of races."
        )
    
        return

    races = load_all_races(
        race_files
    )

    race_labels = {}

    for i, path in enumerate(
        race_files,
        start=1,
    ):
    
        parts = path.stem.split("_")
    
        race_name = parts[0]
    
        race_date = datetime.strptime(
            parts[2],
            "%d%m%Y"
        )
    
        label = (
            f"{race_name} "
            f"({race_date.strftime('%d %b')})"
        )
    
        race_labels[
            f"race_{i}_pos"
        ] = label

    
    print(
        f"Loaded {len(races)} races."
    )
    
    for race in races:
    
        print(
            f"  {len(race)} competitors"
        )

    merged = merge_n_races(
        races
    )
    
    print(
        "\nMerged dataframe:"
    )
    
    print(
        merged.shape
    )

    position_cols = [
        c
        for c in merged.columns
        if c.endswith("_pos")
    ]
    
    print(
        "\nPosition columns:"
    )
    
    for col in position_cols:
    
        print(
            f"  {col}"
        )

    fleet_size = len(
        merged
    )
    
    dnc_score = (
        fleet_size + 1
    )
    
    print(
        f"\nFleet size: {fleet_size}"
    )
    
    print(
        f"DNC score: {dnc_score}"
    )

    for col in position_cols:
    
        merged[col] = (
            pd.to_numeric(
                merged[col],
                errors="coerce"
            )
            .fillna(
                dnc_score
            )
        )

    score_table = pd.DataFrame()
    
    score_table[
        "competitor_id"
    ] = merged[
        "competitor_id"
    ]
    
    score_table[
        "Boat"
    ] = merged[
        "boat_type"
    ].fillna(
        merged[
            "boat_type_y"
        ]
    ).fillna(
        merged[
            "boat_type_x"
        ]
    )
    
    score_table[
        "Sail Number"
    ] = merged[
        "sail_number"
    ].fillna(
        merged[
            "sail_number_y"
        ]
    ).fillna(
        merged[
            "sail_number_x"
        ]
    )
    
    score_table[
        "Sail Number"
    ] = score_table[
        "Sail Number"
    ].apply(
        lambda x:
        (
            str(int(float(x)))
            if str(x).replace(".","").isdigit()
            else str(x)
        )
    )


    score_table[
        "Helm"
    ] = merged[
        "helm"
    ].fillna(
        merged[
            "helm_y"
        ]
    ).fillna(
        merged[
            "helm_x"
        ]
    )
    
    score_table[
        "Crew"
    ] = merged[
        "crew"
    ].fillna(
        merged[
            "crew_y"
        ]
    ).fillna(
        merged[
            "crew_x"
        ]
    ).fillna( "" )
    
    for race_index, col in enumerate(
        position_cols
    ):

        display_values = []

        for row_index in merged.index:

            score = int(
                merged.loc[
                    row_index,
                    col
                ]
            )

            status_col = (
                f"race_{race_index + 1}_status"
            )

            if status_col in merged.columns:

                status = str(
                    merged.loc[
                        row_index,
                        status_col
                    ]
                ).upper()

            else:

                status = ""

            #
            # DNC
            #

            if score == dnc_score:

                text = (
                    f"{score} DNC"
                )

            #
            # RET / DNF / DNS
            #

            elif status in [
                "RET",
                "DNF",
                "DNS",
            ]:

                text = (
                    f"{score} {status}"
                )

            else:

                text = str(
                    score
                )

            #
            # Discard
            #

            race_scores = []

            for race_col in position_cols:

                race_scores.append(
                    merged.loc[
                        row_index,
                        race_col
                    ]
                )

            discard_index = race_scores.index(
                max(
                    race_scores
                )
            )

            if race_index == discard_index:

                text = (
                    f"({text})"
                )

            display_values.append(
                text
            )

        score_table[
            race_labels[col]
        ] = display_values




    #
    # Calculate scores from the original numeric race columns.
    # Do not calculate from the formatted display strings.
    #

    numeric_scores = merged[
        position_cols
    ].copy()

    score_table[
        "Total Score"
    ] = numeric_scores.sum(
        axis=1
    )

    def calculate_net_score(row):

        scores = sorted(
            [
                float(value)
                for value in row
            ],
            reverse=True,
        )

        discarded_scores = scores[
            :discards
        ]

        return (
            sum(scores)
            -
            sum(discarded_scores)
        )

    score_table[
        "Net Score"
    ] = numeric_scores.apply(
        calculate_net_score,
        axis=1,
    )

    score_table = (
        score_table
        .sort_values(
            "Net Score"
        )
        .reset_index(
            drop=True
        )
    )

    score_table.insert(
        0,
        "Position",
        range(
            1,
            len(score_table) + 1
        )
    )


    OUTPUT_DIR = Path(
        "results/Series"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    safe_name = (
        series_name
        .replace(
            " ",
            "_"
        )
    )


    excel_file = (
        OUTPUT_DIR
        /
        f"{safe_name}.xlsx"
    )


    score_table.to_excel(
        excel_file,
        index=False,
    )


    html_file = (
        OUTPUT_DIR
        /
        f"{safe_name}.html"
    )

    public_table = score_table.drop(
        columns=[
            "competitor_id"
        ]
    )

    table_html = (
        public_table
        .to_html(
            index=False,
            escape=False
        )
    )

    logo_file = Path(
        "img/club_logo.jpg"
    )

    logo_html = ""

    if logo_file.exists():

        logo_data = (
            base64.b64encode(
                logo_file.read_bytes()
            )
            .decode("ascii")
        )

        logo_html = (
            f'<img '
            f'class="club-logo" '
            f'src="data:image/jpeg;base64,{logo_data}" '
            f'alt="Club Logo">'
        )

    html = f"""
    <html>
    <head>
    <title>{series_name}</title>
    
    <style>
    
    body {{
        font-family: Arial, sans-serif;
        margin: 30px;
    }}
    
    .page-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    
    .club-logo {{
        width: 120px;
        height: auto;
    }}


    
    table {{
        border-collapse: collapse;
    }}
    
    th, td {{
        border: 1px solid #cccccc;
        padding: 6px;
    }}
    
    th {{
        background: #003366;
        color: white;
    }}
    
    tr:nth-child(even) {{
        background: #f5f5f5;
    }}
    
    </style>
    
    </head>
    
    <body>
    
    <div class="page-header">
    
        <div>
    
            <h1>{series_name}</h1>
    
            <p>
    
            Race type: {race_type}<br>
            Races: {len(race_files)}<br>
            Discards: {discards}<br>
            Entries: {fleet_size}
    
            </p>
    
        </div>
    
        {logo_html}
    
    </div>

    
    {table_html}
    
    </body>
    </html>
    """
    
    
    with open(
            html_file,
            "w",
            encoding="utf-8",
        ) as handle:
    
            handle.write(
                html
            )
    
    
    print(
            f"\\nSaved Excel: {excel_file}"
        )
    
    print(
            f"Saved HTML: {html_file}"
        )

    webbrowser.open(html_file.resolve().as_uri())




if __name__ == "__main__":

    compile_series()

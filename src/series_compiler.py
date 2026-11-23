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
    results_dir=RESULTS_DIR,
):
    files = []

    for path in Path(results_dir).glob(
        "*_results.xlsx"
    ):

        parts = path.stem.split("_")

        if len(parts) < 4:
            continue

        race_name = parts[0]
        file_race_type = parts[1]

        if file_race_type != race_type:
            continue

        if not race_name.lower().startswith(
            "race"
        ):
            continue

        race_number_text = race_name[4:]

        if not race_number_text.isdigit():
            continue

        race_number = int(
            race_number_text
        )

        date_string = parts[2]

        try:
            race_date = datetime.strptime(
                date_string,
                "%d%m%Y"
            ).date()

        except ValueError:
            continue

        if (
            start_date
            <= race_date
            <= end_date
        ):
            files.append(
                (
                    race_date,
                    race_number,
                    path,
                )
            )

    files.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    return [
        item[2]
        for item in files
    ]


def load_all_races(
    race_files,
    scoring_mode="boat",
):
    races = []

    for i, path in enumerate(
        race_files,
        start=1,
    ):
        race = load_race_results(
            path,
            i
        )

        if scoring_mode == "helm":

            race["helm_key"] = (
                race["helm"]
                .apply(
                    normalise_helm_name
                )
            )

            if (
                race["helm_key"] == ""
            ).any():

                raise ValueError(
                    f"Blank helm name in {path.name}"
                )

            duplicates = race[
                race["helm_key"].duplicated(
                    keep=False
                )
            ]

            if not duplicates.empty:

                duplicate_names = (
                    duplicates["helm"]
                    .astype(str)
                    .tolist()
                )

                raise ValueError(
                    f"Duplicate helm in "
                    f"{path.name}: "
                    f"{duplicate_names}"
                )

        races.append(
            race
        )

    return races

def merge_n_races(
    race_list,
    scoring_mode="boat",
):
    if scoring_mode == "helm":
        merge_key = "helm_key"
    else:
        merge_key = "competitor_id"

    merged = None

    for race_index, race_df in enumerate(
        race_list,
        start=1,
    ):

        race_columns = [
            merge_key,
            f"race_{race_index}_pos",
            f"race_{race_index}_elapsed_time",
            f"race_{race_index}_status",
        ]

        race_columns = [
            col
            for col in race_columns
            if col in race_df.columns
        ]

        race_slice = race_df[
            race_columns
        ].copy()

        if merged is None:
            merged = race_slice
        else:
            merged = merged.merge(
                race_slice,
                on=merge_key,
                how="outer",
            )

    return merged


def apply_series_dnc(
    merged,
    position_cols,
):
    """
    Replace missing race positions with the series
    DNC score: number of unique entries plus one.
    """
    merged = merged.copy()

    fleet_size = len(
        merged
    )

    dnc_score = (
        fleet_size + 1
    )

    for col in position_cols:

        merged[col] = (
            pd.to_numeric(
                merged[col],
                errors="coerce",
            )
            .fillna(
                dnc_score
            )
        )

    return (
        merged,
        fleet_size,
        dnc_score,
    )


def get_discard_count(
    race_count
):
    return race_count // 3

def build_first_metadata(
    race_list,
    scoring_mode,
):
    """
    Return identity metadata from each competitor's first
    chronological appearance in the series.

    In boat mode, competitors are identified by competitor_id.
    In helm mode, competitors are identified by helm_key.
    """
    if scoring_mode == "helm":
        key_col = "helm_key"
    else:
        key_col = "competitor_id"

    metadata_frames = []

    for race in race_list:

        metadata_frames.append(
            race[
                [
                    key_col,
                    "boat_type",
                    "sail_number",
                    "helm",
                    "crew",
                ]
            ].copy()
        )

    metadata = pd.concat(
        metadata_frames,
        ignore_index=True,
    )

    metadata = metadata[
        metadata[key_col].notna()
    ].copy()

    if scoring_mode == "helm":

        metadata = metadata[
            metadata[key_col] != ""
        ].copy()

    metadata = metadata.drop_duplicates(
        subset=[
            key_col
        ],
        keep="first",
    )

    return metadata.set_index(
        key_col
    )


def normalise_helm_name(value):
    """
    Return a stable, case-insensitive key for matching
    the same helm across different races and boats.
    """
    if pd.isna(value):
        return ""

    return " ".join(
        str(value).strip().split()
    ).casefold()


def get_discard_indices(
    race_scores,
    discards,
):
    """
    Return the race indices to exclude from a series score.

    Worst scores are discarded first. For equal scores,
    earlier race indices are selected deterministically.
    """
    if discards <= 0:
        return []

    indexed_scores = [
        (
            index,
            float(score),
        )
        for index, score in enumerate(
            race_scores
        )
    ]

    ranked = sorted(
        indexed_scores,
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    return [
        index
        for index, _ in ranked[
            :discards
        ]
    ]


def calculate_series_net_score(
    race_scores,
    discards,
):
    """
    Calculate series net score after excluding
    the selected worst race results.
    """
    scores = [
        float(score)
        for score in race_scores
    ]

    discard_indices = get_discard_indices(
        scores,
        discards,
    )

    return sum(
        score
        for index, score in enumerate(
            scores
        )
        if index not in discard_indices
    )


def build_tiebreak_key(
    race_scores,
    discards,
):
    """
    World Sailing RRS Appendix A8 series tie-break.

    A8.1:
    Compare non-excluded scores from best to worst.

    A8.2:
    If still tied, compare the last race, then work
    backwards through the series, including excluded scores.
    """
    scores = [
        float(score)
        for score in race_scores
    ]

    ordered = sorted(
        scores,
        reverse=True,
    )

    if discards > 0:
        counted = ordered[
            discards:
        ]
    else:
        counted = ordered

    counted_best_to_worst = sorted(
        counted
    )

    latest_to_earliest = list(
        reversed(scores)
    )

    return tuple(
        counted_best_to_worst
        + latest_to_earliest
    )


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

    if scoring_choice == "1":

        scoring_mode = "boat"

    elif scoring_choice == "2":

        scoring_mode = "helm"

    else:

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
        race_files,
        scoring_mode,
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
        races,
        scoring_mode,
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

    merged, fleet_size, dnc_score = (
        apply_series_dnc(
            merged,
            position_cols,
        )
    )

    print(
        f"\nFleet size: {fleet_size}"
    )

    print(
        f"DNC score: {dnc_score}"
    )

    score_table = pd.DataFrame()

    if scoring_mode == "helm":
        identity_col = "helm_key"
    else:
        identity_col = "competitor_id"

    score_table[
        identity_col
    ] = merged[
        identity_col
    ]

    first_metadata = build_first_metadata(
        races,
        scoring_mode,
    )

    score_table[
        "Boat"
    ] = score_table[
        identity_col
    ].map(
        first_metadata[
            "boat_type"
        ]
    )

    score_table[
        "Sail Number"
    ] = score_table[
        identity_col
    ].map(
        first_metadata[
            "sail_number"
        ]
    )

    def format_sail_number(value):

        if pd.isna(value):
            return ""

        try:
            numeric_value = float(value)

            if numeric_value.is_integer():
                return str(
                    int(numeric_value)
                )

        except (
            TypeError,
            ValueError,
        ):
            pass

        return str(value)

    score_table[
        "Sail Number"
    ] = score_table[
        "Sail Number"
    ].apply(
        format_sail_number
    )

    score_table[
        "Helm"
    ] = score_table[
        identity_col
    ].map(
        first_metadata[
            "helm"
        ]
    )

    score_table[
        "Crew"
    ] = score_table[
        identity_col
    ].map(
        first_metadata[
            "crew"
        ]
    ).fillna("")

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

            discard_indices = get_discard_indices(
                race_scores,
                discards,
            )

            if race_index in discard_indices:

                text = (
                    f"({text})"
                )

            #
            # Podium colours
            #
            if score == 1:
                text = f'<span class="gold">{text}</span>'
            elif score == 2:
                text = f'<span class="silver">{text}</span>'
            elif score == 3:
                text = f'<span class="bronze">{text}</span>'
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

    score_table[
        "Net Score"
    ] = numeric_scores.apply(
        lambda row: calculate_series_net_score(
            row.tolist(),
            discards,
        ),
        axis=1,
    )

    #
    # Series ranking and RRS Appendix A8 tie-break.
    #
    tiebreak_keys = numeric_scores.apply(
        lambda row: build_tiebreak_key(
            row.tolist(),
            discards,
        ),
        axis=1,
    )

    score_table[
        "_tiebreak_key"
    ] = tiebreak_keys

    score_table = (
        score_table
        .sort_values(
            by=[
                "Net Score",
                "_tiebreak_key",
            ],
            ascending=[
                True,
                True,
            ],
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    score_table.drop(
        columns=[
            "_tiebreak_key"
        ],
        inplace=True,
    )

    score_table.insert(
        0,
        "Pos.",
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

    private_id_col = (
        "helm_key"
        if scoring_mode == "helm"
        else "competitor_id"
    )

    public_table = score_table.drop(
        columns=[
            private_id_col
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

    scoring_label = (
        "Helm"
        if scoring_mode == "helm"
        else "Boat"
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
    
    .gold {{ display: block; background-color: #FFD700; font-weight: bold; text-align: center; margin: -6px; padding: 6px; }}
    .silver {{ display: block; background-color: #C0C0C0; font-weight: bold; text-align: center; margin: -6px; padding: 6px; }}
    .bronze {{ display: block; background-color: #CD7F32; font-weight: bold; text-align: center; margin: -6px; padding: 6px; }}

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
            Scores combined on: {scoring_label}<br>
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

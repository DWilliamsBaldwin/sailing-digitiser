#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


OUTPUT_DIR = Path("tests/fixtures/series")


COMPETITORS = [
    {
        "competitor_id": "TEST001",
        "boat_type": "COMET",
        "sail_number": "1001",
        "helm": "Test Helm A",
        "crew": "",
    },
    {
        "competitor_id": "TEST002",
        "boat_type": "SUPERNOVA",
        "sail_number": "2002",
        "helm": "Test Helm B",
        "crew": "",
    },
]


def write_race(
    race_number,
    positions,
    date_code="31122099",
):
    rows = []

    for competitor, position in zip(
        COMPETITORS,
        positions,
    ):
        row = competitor.copy()

        row["race_type"] = "PURSUIT"
        row["elapsed_time"] = ""
        row["total_laps"] = 0
        row["finishing_position"] = position
        row["corrected_position"] = position
        row["race_status"] = "MANUAL_ENTRY"
        row["status"] = "MANUAL_ENTRY"

        rows.append(row)

    df = pd.DataFrame(rows)

    output = (
        OUTPUT_DIR
        / (
            f"Race{race_number}_"
            f"PURS_{date_code}_results.xlsx"
        )
    )

    df.to_excel(
        output,
        index=False,
    )

    return output


def make_identity_test_data():
    """
    Generate dedicated fixtures for testing the difference
    between boat-based and helm-based series aggregation.

    Scenario A:
    One helm sails multiple boats.

    Scenario B:
    Multiple helms sail the same boat.
    """
    identity_dir = (
        Path("tests/fixtures/identity")
    )

    identity_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for old_file in identity_dir.glob(
        "*_results.xlsx"
    ):
        old_file.unlink()

    races = {
        1: [
            {
                "competitor_id": "BOAT3003",
                "boat_type": "COMET",
                "sail_number": "3003",
                "helm": "Test Helm C",
                "crew": "",
                "corrected_position": 1,
            },
            {
                "competitor_id": "BOAT5005",
                "boat_type": "GP14",
                "sail_number": "5005",
                "helm": "Test Helm D",
                "crew": "Test Crew",
                "corrected_position": 2,
            },
        ],

        2: [
            {
                "competitor_id": "BOAT4004",
                "boat_type": "SUPERNOVA",
                "sail_number": "4004",
                "helm": "Test Helm C",
                "crew": "",
                "corrected_position": 1,
            },
            {
                "competitor_id": "BOAT5005",
                "boat_type": "GP14",
                "sail_number": "5005",
                "helm": "Test Helm E",
                "crew": "Test Crew",
                "corrected_position": 2,
            },
        ],

        3: [
            {
                "competitor_id": "BOAT3003",
                "boat_type": "COMET",
                "sail_number": "3003",
                "helm": "Test Helm C",
                "crew": "",
                "corrected_position": 1,
            },
            {
                "competitor_id": "BOAT5005",
                "boat_type": "GP14",
                "sail_number": "5005",
                "helm": "Test Helm D",
                "crew": "Test Crew",
                "corrected_position": 2,
            },
        ],
    }

    for race_number, rows in races.items():

        df = pd.DataFrame(
            rows
        )

        df["elapsed_time"] = ""
        df["race_status"] = "MANUAL_ENTRY"

        output = (
            identity_dir
            / (
                f"Race{race_number}_"
                f"PURS_30122099_results.xlsx"
            )
        )

        df.to_excel(
            output,
            index=False,
        )

        print(
            f"  {output}"
        )


def make_status_test_data():
    """
    Create one pursuit race containing a normal finisher
    plus DNF, DNS and RET results.
    """
    status_dir = Path(
        "tests/fixtures/status"
    )

    status_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    input_file = (
        status_dir
        / "pursuit_status_input.xlsx"
    )

    rows = [
        {
            "competitor_id": "STATUS001",
            "boat_type": "COMET",
            "sail_number": "6001",
            "helm": "Status Helm A",
            "crew": "",
            "finishing_position": 1,
            "status": "MANUAL_ENTRY",
        },
        {
            "competitor_id": "STATUS002",
            "boat_type": "COMET",
            "sail_number": "6002",
            "helm": "Status Helm B",
            "crew": "",
            "finishing_position": "",
            "status": "DNF",
        },
        {
            "competitor_id": "STATUS003",
            "boat_type": "COMET",
            "sail_number": "6003",
            "helm": "Status Helm C",
            "crew": "",
            "finishing_position": "",
            "status": "DNS",
        },
        {
            "competitor_id": "STATUS004",
            "boat_type": "COMET",
            "sail_number": "6004",
            "helm": "Status Helm D",
            "crew": "",
            "finishing_position": "",
            "status": "RET",
        },
    ]

    pd.DataFrame(
        rows
    ).to_excel(
        input_file,
        index=False,
    )

    return input_file


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for old_file in OUTPUT_DIR.glob(
        "*_results.xlsx"
    ):
        old_file.unlink()

    #
    # Ten-race synthetic series.
    #
    # Races 1-4 deliberately provide useful
    # positions for tie-break/ordering tests.
    #
    race_positions = {
        1: [1, 2],
        2: [2, 1],
        3: [1, 2],
        4: [2, 1],
        5: [1, 2],
        6: [2, 1],
        7: [1, 2],
        8: [2, 1],
        9: [1, 2],
        10: [2, 1],
    }

    print(
        "Generating synthetic series fixtures..."
    )

    for race_number in range(
        1,
        11,
    ):
        path = write_race(
            race_number,
            race_positions[
                race_number
            ],
        )

        print(
            f"  {path}"
        )

    print(
        "\nCreated 10 synthetic pursuit races."
    )

    print(
        "\nGenerating identity/aggregation fixtures..."
    )

    make_identity_test_data()

    print(
        "\nCreated identity fixtures."
    )

    print(
        "\nGenerating pursuit status fixture..."
    )

    make_status_test_data()

    print(
        "\nCreated pursuit status fixture."
    )


if __name__ == "__main__":
    main()

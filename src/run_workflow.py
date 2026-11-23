#!/usr/bin/env python3

import subprocess
import webbrowser
import shutil
from datetime import datetime
from pathlib import Path
import process_race_entry as manual
from series_compiler import compile_series

def run_command(command):

    print("\nRunning:")

    print(
        " ".join(command)
    )

    result = subprocess.run(
        command,
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Command failed: {' '.join(command)}"
        )


def open_file(path):

    path = Path(path).resolve()

    webbrowser.open(
        path.as_uri()
    )


def wait_for_user(message):

    input(
        f"\n{message}\n"
        "Press ENTER when ready..."
    )


def archive_race_result(
    race_num,
    race_type,
    race_date,
    source_file,
):
    results_dir = Path("results")
    results_dir.mkdir(
        exist_ok=True
    )

    race_code = {
        "HANDICAP": "HAND",
        "PURSUIT": "PURS",
    }.get(
        race_type,
        race_type,
    )

    date_code = race_date.strftime(
        "%d%m%Y"
    )

    archive_file = (
        results_dir
        / (
            f"Race{race_num}_"
            f"{race_code}_"
            f"{date_code}_results.xlsx"
        )
    )

    if archive_file.exists():
        print(
            "\nWARNING: Archived result "
            "already exists:"
        )
        print(
            archive_file
        )

        overwrite = input(
            "Overwrite it? (Y/N): "
        ).strip().upper()

        if overwrite != "Y":
            print(
                "\nExisting archived result "
                "has been preserved."
            )
            return

    shutil.copy2(
        source_file,
        archive_file,
    )

    print(
        "\nPermanent race result saved:"
    )
    print(
        archive_file
    )

def build_pursuit_results(
    race_workbook,
    race_results_file,
):
    import pandas as pd

    df = pd.read_excel(
        race_workbook
    )

    competitor_count = len(df)
    penalty_score = competitor_count + 1

    df["race_status"] = (
        df["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["corrected_position"] = (
        pd.to_numeric(
            df["finishing_position"],
            errors="coerce",
        )
    )

    special_statuses = [
        "DNF",
        "DNS",
        "RET",
    ]

    special_mask = (
        df["race_status"]
        .isin(special_statuses)
    )

    df.loc[
        special_mask,
        "corrected_position",
    ] = penalty_score

    df["corrected_position"] = (
        df["corrected_position"]
        .astype("Int64")
    )

    df.sort_values(
        "corrected_position",
        inplace=True,
    )

    df.to_excel(
        race_results_file,
        index=False,
    )

    print(
        f"Created {race_results_file}"
    )

def process_race(race_num):

    print(
        f"\n========== RACE {race_num} ==========\n"
    )

    mode = input(
        "Entry mode "
        "(OCR/MANUAL): "
    ).strip().upper()

    race_type = input(
        "Race type "
        "(HANDICAP/PURSUIT): "
    ).strip().upper()

    while True:
        race_date_input = input(
            "Race date "
            "(DD/MM/YYYY): "
        ).strip()

        try:
            race_date = datetime.strptime(
                race_date_input,
                "%d/%m/%Y",
            )
            break

        except ValueError:
            print(
                "Invalid date. "
                "Please use DD/MM/YYYY."
            )

    race_name = f"race{race_num}"



    validation_file = (
        f"output/{race_name}_validation.xlsx"
    )
    
    race_workbook = (
        f"output/{race_name}.xlsx"
    )
    
    race_results_file = (
        f"output/{race_name}_results.xlsx"
    )

    if mode == "OCR":
    
            image_file = input(
                f"Path to Race {race_num} image: "
            ).strip()
        
            expected_sails = input(
                "Expected sail numbers "
                "(comma separated): "
            ).strip()

            run_command(
                [
                    "python",
                    "src/process_race_sheet.py",
                    "--image",
                    image_file,
                    "--race-label",
                    f"race{race_num}",
                    "--expected-sails",
                    expected_sails,
                ]
            )
    
    else:
    
        sailors_df = (
            manual.load_sailors()
        )
    
        fleet = (
            manual.build_fleet(
                sailors_df
            )
        )
    
        results_df = (
            manual.enter_results(
                fleet,
                race_type,
            )
        )
    
        manual.write_validation_file(
            results_df,
            race_name,
        )

    print(
        "\nGenerating validation workbook..."
    )

    print(
        "\nOpening validation workbook..."
    )

    open_file(
        validation_file
    )

    wait_for_user(
        "Review validation workbook.\n\n"
        "Correct any values.\n"
        "Set UPDATE_SAILOR where required.\n"
        "Save and close the workbook."
    )

    print(
        "\nBuilding race workbook..."
    )

    run_command(
        [
            "python",
            "src/build_race_workbook.py",
            "--validation",
            validation_file,
            "--sailors",
            "data/reference/sailors.csv",
            "--output",
            race_workbook,
        ]
    )

    if race_type == "HANDICAP":
        print(
            "\nRunning handicap calculator..."
        )

        run_command(
            [
                "python",
                "src/handicap_calculator.py",
                "--race",
                race_workbook,
                "--py",
                "data/reference/py_lookup.csv",
                "--output",
                race_results_file,
            ]
        )

    elif race_type == "PURSUIT":
        print(
            "\nPreparing pursuit race results..."
        )
    
        build_pursuit_results(
            race_workbook,
            race_results_file,
        )

    else:
        raise ValueError(
            f"Unknown race type: {race_type}"
        )

    # Archive the completed result for either race type.
    archive_race_result(
        race_num,
        race_type,
        race_date,
        race_results_file,
    )

    print(
        f"\nRace {race_num} complete."
    )


def rebuild_existing_race():

    race_num = input(
        "\nRace number to rebuild: "
    ).strip()

    try:
        race_num_value = int(
            race_num
        )

        if race_num_value < 1:
            raise ValueError

    except ValueError:

        print(
            "\nRace number must be "
            "a positive integer."
        )

        return

    race_num = str(
        race_num_value
    )

    validation_file = (
        f"output/race{race_num}_validation.xlsx"
    )

    if not Path(
        validation_file
    ).exists():

        print(
            f"\n{validation_file} "
            "does not exist."
        )

        return

    race_workbook = (
        f"output/race{race_num}.xlsx"
    )

    race_results_file = (
        f"output/race{race_num}_results.xlsx"
    )

    print(
        f"\nRebuilding Race {race_num}"
    )

    run_command(
        [
            "python",
            "src/build_race_workbook.py",
            "--validation",
            validation_file,
            "--sailors",
            "data/reference/sailors.csv",
            "--output",
            race_workbook,
        ]
    )

    run_command(
        [
            "python",
            "src/handicap_calculator.py",
            "--race",
            race_workbook,
            "--py",
            "data/reference/py_lookup.csv",
            "--output",
            race_results_file,
        ]
    )

    print(
        f"\nRace {race_num} rebuilt."
    )

def rebuild_existing_results():

    for race_num in [1, 2, 3]:

        validation_file = (
            f"output/race{race_num}_validation.xlsx"
        )

        if not Path(
            validation_file
        ).exists():

            continue

        race_workbook = (
            f"output/race{race_num}.xlsx"
        )

        race_results = (
            f"output/race{race_num}_results.xlsx"
        )

        print(
            f"\nRebuilding race {race_num}"
        )

        run_command(
            [
                "python",
                "src/build_race_workbook.py",
                "--validation",
                validation_file,
                "--sailors",
                "data/reference/sailors.csv",
                "--output",
                race_workbook,
            ]
        )

        run_command(
            [
                "python",
                "src/handicap_calculator.py",
                "--race",
                race_workbook,
                "--py",
                "data/reference/py_lookup.csv",
                "--output",
                race_results,
            ]
        )

    generate_final_standings()

def generate_final_standings():

    print(
        "\nGenerating final standings..."
    )

    run_command(
        [
            "python",
            "src/series_scorer.py",
            "--race1",
            "output/race1_results.xlsx",
            "--race2",
            "output/race2_results.xlsx",
            "--race3",
            "output/race3_results.xlsx",
            "--output",
            "output/final_standings.xlsx",
        ]
    )

    print(
        "\nOpening final standings..."
    )

    open_file(
        "final_standings.html"
    )

    print(
        "\nFinal standings complete."
    )


if __name__ == "__main__":

    while True:

        print(
            "\n====================================="
        )

        print(
            "      Sailing Digitiser"
        )

        print(
            "====================================="
        )

        print(
            "\n1 - Process a Race"
        )

        print(
            "2 - Generate Final Standings"
        )

        print(
            "3 - Rebuild Existing Race"
        )

        print(
            "4 - Rebuild Existing Results"
        )

        print(
            "5 - Compile New Series"
        )

        print(
            "6 - Exit"
        )



        choice = input(
            "\nSelect option: "
        ).strip()

        if choice == "1":

            race_num_input = input(
                "\nRace number: "
            ).strip()

            try:
                race_num = int(
                    race_num_input
                )

                if race_num < 1:
                    raise ValueError

            except ValueError:
                print(
                    "\nRace number must be "
                    "a positive integer."
                )
                continue

            process_race(
                race_num
            )

        elif choice == "2":

            generate_final_standings()

        elif choice == "3":

            rebuild_existing_race()

        elif choice == "4":

            rebuild_existing_results()

        elif choice == "5":

            compile_series()

        elif choice == "6":

            print(
                "\nGoodbye."
            )

            break

        else:

            print(
                "\nInvalid option."
            )

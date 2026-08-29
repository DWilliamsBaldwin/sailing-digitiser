#!/usr/bin/env python3

import subprocess
import webbrowser
from pathlib import Path


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


def process_race(race_num):

    print(
        f"\n========== RACE {race_num} ==========\n"
    )

    image_file = input(
        f"Path to Race {race_num} image: "
    ).strip()

    validation_file = (
        f"output/race{race_num}_validation.xlsx"
    )

    race_workbook = (
        f"output/race{race_num}.xlsx"
    )

    race_results_file = (
        f"output/race{race_num}_results.xlsx"
    )

    print(
        "\nGenerating validation workbook..."
    )

    run_command(
        [
            "python",
            "src/process_race_sheet.py",
            "--image",
            image_file,
            "--race-label",
            f"race{race_num}",
        ]
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

    print(
        f"\nRace {race_num} complete."
    )


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
            "\n1 - Process Race 1"
        )

        print(
            "2 - Process Race 2"
        )

        print(
            "3 - Process Race 3"
        )

        print(
            "4 - Generate Final Standings"
        )

        print(
            "5 - Exit"
        )

        choice = input(
            "\nSelect option: "
        ).strip()

        if choice == "1":

            process_race(1)

        elif choice == "2":

            process_race(2)

        elif choice == "3":

            process_race(3)

        elif choice == "4":

            generate_final_standings()

        elif choice == "5":

            print(
                "\nGoodbye."
            )

            break

        else:

            print(
                "\nInvalid option."
            )

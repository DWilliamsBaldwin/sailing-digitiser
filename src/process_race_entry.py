#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

def load_sailors():

    sailors_df = pd.read_csv(
        "data/reference/sailors.csv",
        dtype=str,
        index_col=False,
    )

    sailors_df["Sail No"] = (
        sailors_df["Sail No"]
        .astype(str)
        .str.strip()
    )

    return sailors_df

def build_fleet(sailors_df):

    fleet = []

    while True:

        sail = input(
            "\nSail number "
            "(blank to finish): "
        ).strip()

        if sail == "":
            break

        matches = sailors_df[
            sailors_df["Sail No"] == sail
        ]

        if len(matches) == 1:

            sailor = matches.iloc[0]

            boat_type = sailor["Class"]

            if boat_type.upper().startswith("ILCA"):
            
                print("\nSelect rig:")
            
                print("1 - ILCA 4")
                print("2 - ILCA 6")
                print("3 - ILCA 7")
            
                choice = input(
                    "Choice: "
                ).strip()
            
                rig_lookup = {
                    "1": "ILCA 4",
                    "2": "ILCA 6",
                    "3": "ILCA 7",
                }
            
                boat_type = rig_lookup.get(
                    choice,
                    "ILCA 7",
                )


            print("\nFound:")

            print(
                f"Sail: {sail}"
            )

            print(
                f"Helm: "
                f"{sailor['Helm Name']}"
            )

            print(
                f"Crew: "
                f"{sailor['Crew Name']}"
            )
            
            print(
                f"Class: "
                f"{sailor['Class']}"
            )


            confirm = input(
                "\nUse this sailor? "
                "(Y/N): "
            ).strip().upper()

            if confirm == "Y":
            
                fleet.append(
                    {
                        "sail_number": sail,
                        "helm": sailor["Helm Name"],
                        "crew": sailor["Crew Name"],
                        "boat_type": boat_type,
                    }
                )
            
            else:
            
                helm = input(
                    "Correct helm: "
                ).strip()
            
                crew = input(
                    "Correct crew: "
                ).strip()
            
                boat_type = input(
                    "Correct class: "
                ).strip()
            
                fleet.append(
                    {
                        "sail_number": sail,
                        "helm": helm,
                        "crew": crew,
                        "boat_type": boat_type,
                    }
                )


        else:


            print(
                "\nSail number not found."
            )
            
            add_manual = input(
                "Add sailor manually? "
                "(Y/N): "
            ).strip().upper()
            
            if add_manual == "Y":
            
                helm = input(
                    "Helm: "
                ).strip()
            
                crew = input(
                    "Crew (blank if none): "
                ).strip()
            
                boat_type = input(
                     "Class: "
                ).strip()
            
                fleet.append(
                    {
                        "sail_number": sail,
                        "helm": helm,
                        "crew": crew,
                        "boat_type": boat_type,
                    }
                )

    print("\n=== FLEET ===\n")
    
    for sailor in fleet:
    
        print(
            f"{sailor['sail_number']} "
            f"{sailor['helm']} "
            f"({sailor['boat_type']})"
        )


    return fleet

def enter_results(fleet,race_type,):

    rows = []

    print(
        "\n=== ENTER RESULTS ==="
    )

    for sailor in fleet:

        print(
            f"\n{sailor['sail_number']}"
        )

        print(
            sailor["helm"]
        )

        elapsed = input(
            "Elapsed time "
            "(MM:SS, DNF, DNS or RET): "
        ).strip().upper()


        if "." in elapsed:
            elapsed = elapsed.replace(
                ".",
                ":",
            )

        if elapsed in [
            "DNF",
            "DNS",
            "RET",
        ]:
  
            rows.append(
                {
                    **sailor,
                    "race_type": race_type, 
                    "elapsed_time": elapsed, 
                    "total_laps": 0,
                    "raw_sail_number":
                        sailor["sail_number"],
                    "raw_helm":
                        sailor["helm"],
                    "raw_crew":
                        sailor["crew"],
                    "raw_boat_type":
                        sailor["boat_type"],
                    "corrected_sail_number":
                        sailor["sail_number"],
                    "corrected_helm":
                        sailor["helm"],
                    "corrected_crew":
                        sailor["crew"],
                    "corrected_class":
                        sailor["boat_type"],
                    "confidence": 1.0,
                    "status": elapsed,
                }
            )
        
            continue
        
        laps = input(
            "Laps sailed: "
        ).strip()


        rows.append(
            {
                **sailor,
                "race_type": race_type, 
                "elapsed_time": elapsed, 
                "total_laps": int(laps),
                "raw_sail_number":
                    sailor[
                        "sail_number"
                    ],
                "raw_helm":
                    sailor[
                        "helm"
                    ],
                "raw_crew":
                    sailor[
                        "crew"
                    ],
                "raw_boat_type":
                    sailor[
                        "boat_type"
                    ],
                "corrected_sail_number":
                    sailor[
                        "sail_number"
                    ],
                "corrected_helm":
                    sailor[
                        "helm"
                    ],
                "corrected_crew":
                    sailor[
                        "crew"
                    ],
                "corrected_class":
                    sailor[
                        "boat_type"
                    ],
                "confidence":
                    1.0,
                "status":
                    "MANUAL_ENTRY",
            }
        )

    return pd.DataFrame(rows)

#def write_validation_file(df,race_name,):
#
#
#    output_dir = Path(
#        "output"
#    )
#
#    output_dir.mkdir(
#        exist_ok=True
#    )
#
#    output_file = (
#        output_dir
#        / f"{race_name}_validation.xlsx"
#    )
#
#
#    df.to_excel(
#        output_file,
#        index=False,
#    )
#
#    print(
#        f"\nCreated "
#        f"{output_file}"
#    )

def write_validation_file(df, race_name):

    output_dir = Path(
        "output"
    )

    output_dir.mkdir(
        exist_ok=True
    )

    output_file = (
        output_dir
        / f"{race_name}_validation.xlsx"
    )

    validation_df = df[
        [
            "sail_number",
            "helm",
            "crew",
            "boat_type",
            "race_type",
            "elapsed_time",
            "total_laps",
            "status",
        ]
    ].copy()

    validation_df.to_excel(
        output_file,
        index=False,
    )

    print(
        f"\nCreated "
        f"{output_file}"
    )



if __name__ == "__main__":

    print(
        "This module is intended "
        "to be called from "
        "run_workflow.py"
    )

if __name__ == "__main__":

    sailors_df = load_sailors()

    fleet = build_fleet(
        sailors_df
    )

    results_df = enter_results(
        fleet,
        "HANDICAP",
    )

    write_validation_file(
        results_df,
        "test_race",
    )


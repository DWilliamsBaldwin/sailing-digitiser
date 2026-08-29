#!/usr/bin/env python3

import argparse
from ollama import chat
from difflib import SequenceMatcher
from difflib import SequenceMatcher
import pandas as pd
from pathlib import Path


#PROMPT = """
#This is a sailing handicap race scoresheet.

#Extract every competitor visible.

#For each competitor output:

#boat_type,sail_number,helm,crew,elapsed_time,total_laps

#Return CSV rows only.

#Do not explain anything.
#Do not describe the image.
#Do not include markdown.
#"""

#PROMPT = """
#	This is a sailing race scoresheet.
#
#	Extract every competitor visible.
#
#	For each competitor provide:
#
#	SAIL_NUMBER | HELM_CREW
#
#	Read as many competitors as possible.
#
#	Return only competitor entries.
#
#	Do not explain anything.
#	"""

#PROMPT = """
#	This is a sailing handicap race scoresheet.
	#
#	Each competitor row contains a sequence of lap times.
	#
#	The lap columns are labelled:
#	1, 2, 3, 4, 5, 6
	#
#	A competitor's TOTAL_LAPS is the number of lap columns that contain a time.
	#
#	Ignore blank cells and long dashes.
	#
#	The ELAPSED_TIME is the final recorded lap time in the row.
	#
#	Examples:
	#
#	23:01 | 34:50 | 46:10 | 58:22
#	TOTAL_LAPS = 4
#	ELAPSED_TIME = 58:22
	#
#	24:15 | 37:30 | 49:12 | —
#	TOTAL_LAPS = 3
#	ELAPSED_TIME = 49:12
	#
#	For each competitor output:
	#
#	SAIL_NUMBER | ELAPSED_TIME | TOTAL_LAPS
	#
#	Return only competitor entries.
#"""

IDENTITY_PROMPT = """
This is a sailing handicap race results sheet.

Your task is OCR transcription only.

Do NOT calculate elapsed time.
Do NOT calculate total laps.
Do NOT interpret the results.
Do NOT summarise the table.

For each competitor row:

1. Read the boat type.
2. Read the sail number.
3. Read the helm name.
4. Read the crew name if present.

If a value is missing write BLANK.

Do not invent values.
Do not skip competitors.

Return exactly:

BOAT_TYPE | SAIL_NUMBER | HELM | CREW

Example:

ALBACORE | 8065 | PETE CHAMBERS | ERIC HASELDEN

SUPERNOVA | 1321 | JONATHAN LATHAM | BLANK

Return competitor rows only.
Do not include any explanation.
"""


LAP_PROMPT = """
	This is a sailing handicap race results sheet.

	Your task is OCR transcription only.
	
	Do NOT calculate elapsed time.
	Do NOT calculate total laps.
	Do NOT interpret the results.
	Do NOT summarise the table.
	
	For each competitor row:
	
	1. Read the sail number.
	2. Read every visible lap-time cell.
	3. Preserve the order of the lap columns exactly as shown.
	4. If a cell is blank, write BLANK.
	5. If a long dash appears, write DASH.
	6. Do not invent values.
	7. Do not skip competitors.
	
	Return one line per competitor using exactly this format:
	
	SAIL_NUMBER | LAP1 | LAP2 | LAP3 | LAP4 | LAP5 | LAP6
	
	Example:
	
	8065 | 11:12 | 22:54 | 34:31 | 46:10 | DASH | DASH
	
	321 | 12:04 | 24:10 | 36:55 | DASH | DASH | DASH
	
	Important:
	
	The final lap time may be in any lap column.
	Do NOT attempt to determine elapsed time.
	Do NOT attempt to determine number of laps sailed.
	
	Simply transcribe the values visible in each row.
	Return competitor rows only.
"""

def extract_identity_data(image_path):

    print("Sending identity prompt to Ollama...")

    response = chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": IDENTITY_PROMPT,
                "images": [image_path],
            }
        ],
    )

    print("Received identity response")

    return response["message"]["content"]


def extract_race_sheet(image_path):

    print("Sending lap prompt to Ollama...")

    response = chat(
        model="qwen2.5vl:3b",
        messages=[
            {
                "role": "user",
                "content": LAP_PROMPT,
                "images": [image_path],
            }
        ],
    )

    print("Received response from Ollama")

    return response["message"]["content"]


def similarity(a, b):

    if pd.isna(a) or pd.isna(b):
        return 0.0

    return SequenceMatcher(
        None,
        str(a).upper().strip(),
        str(b).upper().strip(),
    ).ratio()


def assign_status(score):

    if score >= 0.95:
        return "AUTO_CORRECT"

    if score >= 0.80:
        return "REVIEW"

    return "LOW_CONFIDENCE"


def correct_against_reference(
    merged_df,
    sailors_df,
):

    corrected_rows = []

    for _, row in merged_df.iterrows():

        extracted_sail = str(
            row["sail_number"]
        ).strip()

        extracted_helm = str(
            row["helm"]
        ).strip()

        extracted_crew = str(
            row["crew"]
        ).strip()

        extracted_boat = str(
            row["boat_type"]
        ).strip()

        best_score = 0
        best_match = None

        #
        # FIRST TRY EXACT SAIL NUMBER MATCH
        #
        exact_match = sailors_df[
            sailors_df["Sail No"].astype(str)
            == extracted_sail
        ]

        if len(exact_match) == 1:

            best_match = exact_match.iloc[0]
            best_score = 1.0

        else:

            #
            # FALL BACK TO FUZZY MATCHING
            #
            for _, ref in sailors_df.iterrows():

                ref_sail = str(
                    ref["Sail No"]
                ).strip()

                ref_helm = str(
                    ref["Helm Name"]
                ).strip()

                ref_crew = str(
                    ref["Crew Name"]
                ).strip()

                ref_class = str(
                    ref["Class"]
                ).strip()

                sail_score = similarity(
                    extracted_sail,
                    ref_sail,
                )

                helm_score = similarity(
                    extracted_helm,
                    ref_helm,
                )

                crew_score = similarity(
                    extracted_helm,
                    ref_crew,
                )

                name_score = max(
                    helm_score,
                    crew_score,
                )

                boat_score = similarity(
                    extracted_boat,
                    ref_class,
                )

                combined_score = (
                    sail_score * 0.50
                    + name_score * 0.40
                    + boat_score * 0.10
                )

                if combined_score > best_score:

                    best_score = combined_score
                    best_match = ref

        status = assign_status(
            best_score
        )

        if (
            best_match is None
            or status == "NOT_IN_REFERENCE"
        ):

            corrected_rows.append(
                {
                    "raw_sail_number":
                        extracted_sail,

                    "raw_helm":
                        extracted_helm,

                    "raw_crew":
                        extracted_crew,

                    "raw_boat_type":
                        extracted_boat,

                    "corrected_sail_number":
                        "",

                    "corrected_helm":
                        "",

                    "corrected_class":
                        "",

                    "corrected_crew":
                        "",

                    "confidence":
                        round(
                            best_score,
                            3,
                        ),

                    "status":
                        status,
                }
            )

        else:

            corrected_rows.append(
                {
                    "raw_sail_number":
                        extracted_sail,

                    "raw_helm":
                        extracted_helm,

                    "raw_crew":
                        extracted_crew,

                    "raw_boat_type":
                        extracted_boat,

                    "corrected_sail_number":
                        best_match["Sail No"],

                    "corrected_helm":
                        best_match["Helm Name"],

                    "corrected_class":
                        best_match["Class"],

                    "corrected_crew":
                        best_match["Crew Name"],

                    "confidence":
                        round(
                            best_score,
                            3,
                        ),

                    "status":
                        status,
                }
            )

    return pd.DataFrame(
        corrected_rows
    )


def parse_identity_output(raw_text):

    rows = []

    for line in raw_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Skip headers
        if "BOAT_TYPE" in line.upper():
            continue

        if "---" in line:
            continue

        if "|" not in line:
            continue

        parts = [
            p.strip()
            for p in line.split("|")
        ]

        # Remove empty columns caused by
        # leading/trailing pipes
        parts = [
            p for p in parts
            if p != ""
        ]

        if len(parts) != 4:
            continue

        boat_type = parts[0]
        sail_number = parts[1]
        helm = parts[2]
        crew = parts[3]

        if crew.upper() in [
            "BLANK",
            "NONE",
            "N/A",
            "-"
        ]:
            crew = ""

        rows.append(
            {
                "boat_type":
                    boat_type,

                "sail_number":
                    sail_number,

                "helm":
                    helm,

                "crew":
                    crew,
            }
        )

    return pd.DataFrame(rows)

def derive_elapsed_time(row):

    lap_cols = [
        "lap1",
        "lap2",
        "lap3",
        "lap4",
        "lap5",
        "lap6",
    ]

    valid = []

    for col in lap_cols:

        value = str(
            row[col]
        ).strip()

        if value.upper() != "BLANK":
            valid.append(value)

    if len(valid) == 0:
        return ""

    return valid[-1]

def derive_total_laps(row):

    lap_cols = [
        "lap1",
        "lap2",
        "lap3",
        "lap4",
        "lap5",
        "lap6",
    ]

    return sum(
        str(row[col]).upper() != "BLANK"
        for col in lap_cols
    )

def parse_lap_output(raw_text):

    rows = []

    for line in raw_text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Skip headers
        if "SAIL_NUMBER" in line.upper():
            continue

        if "---" in line:
            continue

        if "|" not in line:
            continue

        parts = [
            p.strip()
            for p in line.split("|")
        ]

        # Remove empty columns caused by
        # leading/trailing pipes
        parts = [
            p for p in parts
            if p != ""
        ]

        if len(parts) != 7:
            continue

        sail_number = parts[0]

        rows.append(
            {
                "sail_number": sail_number,
                "lap1": parts[1],
                "lap2": parts[2],
                "lap3": parts[3],
                "lap4": parts[4],
                "lap5": parts[5],
                "lap6": parts[6],
            }
        )

    return pd.DataFrame(rows)


def sail_similarity(a, b):

    return SequenceMatcher(
        None,
        str(a),
        str(b),
    ).ratio()


def match_identity_to_laps(
    identity_df,
    laps_df,
    threshold=0.75,
):

    merged_rows = []

    used_lap_indices = set()

    for _, identity_row in identity_df.iterrows():

        identity_sail = str(
            identity_row["sail_number"]
        ).strip()

        best_score = 0
        best_idx = None

        for lap_idx, lap_row in laps_df.iterrows():

            if lap_idx in used_lap_indices:
                continue

            lap_sail = str(
                lap_row["sail_number"]
            ).strip()

            score = sail_similarity(
                identity_sail,
                lap_sail,
            )

            if score > best_score:
                best_score = score
                best_idx = lap_idx

        if (
            best_idx is not None
            and best_score >= threshold
        ):

            used_lap_indices.add(
                best_idx
            )

            lap_row = laps_df.loc[
                best_idx
            ]

            merged_rows.append(
                {
                    **identity_row.to_dict(),
                    **lap_row.to_dict(),
                    "match_confidence":
                        round(
                            best_score,
                            3,
                        ),
                }
            )

        else:

            merged_rows.append(
                {
                    **identity_row.to_dict(),
                    "match_confidence":
                        0,
                }
            )

    return pd.DataFrame(
        merged_rows
    )

def assign_status(score):

    if score >= 0.95:
        return "EXACT_MATCH"

    if score >= 0.85:
        return "HIGH_CONFIDENCE_MATCH"

    if score >= 0.70:
        return "REVIEW_REQUIRED"

    return "NOT_IN_REFERENCE"


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Extract race sheet data using Ollama"
    )

    parser.add_argument(
        "--image",
        required=True,
        help="Path to race sheet image"
    )

    args = parser.parse_args()

    result1 = extract_identity_data(
        args.image
    )

    result2 = extract_race_sheet(
        args.image
    )

    print("\n===== RAW OLLAMA OUTPUT =====\n")

    print(result1)
    print(result2)

    print("\n====== MERGE DATAFRAMES =====\n")

    identity_df = parse_identity_output(result1)
	
    laps_df = parse_lap_output(result2)

    merged_df = match_identity_to_laps(
        identity_df,
        laps_df,
    )

    merged_df["elapsed_time"] = (
        merged_df.apply(
            derive_elapsed_time,
            axis=1,
        )
    )
	
    merged_df["total_laps"] = (
        merged_df.apply(
            derive_total_laps,
            axis=1,
		)
	)

    print(merged_df[
            [
                "sail_number",
                "match_confidence",
            ]
        ]
    )

    sailors_df = pd.read_csv(
        "data/reference/sailors.csv",
        dtype=str,
    )
    
    validation_only_df = (
        correct_against_reference(
            merged_df,
            sailors_df,
        )
    )

    validation_df = pd.concat(
        [
            merged_df.reset_index(drop=True),
            validation_only_df.reset_index(drop=True),
        ],
        axis=1,
    )

    validation_df = validation_df[
        validation_df["total_laps"] > 0
    ].copy()

    column_order = [
	
        # OCR identity
        
        "boat_type",
        "sail_number",
        "helm",
        "crew",
        
        # OCR lap data
        
        "lap1",
        "lap2",
        "lap3",
        "lap4",
        "lap5",
        "lap6",
        
        "elapsed_time",
        "total_laps",
        
        "match_confidence",
        
        # validation
        
        "raw_sail_number",
        "raw_helm",
        "raw_crew",
        "raw_boat_type",
        
        "corrected_sail_number",
        "corrected_helm",
        "corrected_crew",
        "corrected_class",
        
        "confidence",
        "status",
    ]
	
    validation_df = validation_df[
        [
            c
            for c in column_order
            if c in validation_df.columns
        ]
    ]
    
    print(
        validation_df[
            [
                "raw_sail_number",
                "corrected_sail_number",
                "raw_helm",
                "corrected_helm",
                "confidence",
            ]
        ]
    )

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    

    merged_df.to_excel(
        output_dir / "merged_race_data.xlsx",
        index=False,
    )
    
    validation_df.to_excel(
        output_dir / "validation.xlsx",
        index=False,
    )


    validation_file = output_dir / "validation.xlsx"
    
    validation_df.to_excel(
        validation_file,
        index=False,
    )
    
    print(
        f"Created {validation_file}"
    )


    
    print("Created merged_race_data.xlsx")
    print("Created validation.xlsx")

    print("\n===== CHECK OUTPUT =====\n")
    print("\n Make sure to check the \n")
    print("\n= newly created file: ==\n")
    print("\n=== validation.xlsx ====\n")


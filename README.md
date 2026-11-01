# Sailing Digitiser

A local workflow for digitising, validating, processing and scoring
sailing race results.

## Current version

v0.2

The project has developed from an experimental AI/OCR scoresheet
digitiser into an end-to-end race processing workflow.

## Features

### Manual race entry

- Select competitors from a reference sailor database
- Persistent CompetitorID values (`WFSC####`)
- Manual entry of race results
- Validation workbook for checking and correcting data
- UPDATE_SAILOR support for updating existing competitors
- Automatic creation of CompetitorID values for new competitors

### Handicap racing

- Record elapsed time and laps sailed
- Portsmouth Yardstick handicap calculation
- Corrected finishing positions
- DNF, DNS and RET handling

### Pursuit racing

- Enter finishing positions directly
- DNF, DNS and RET handling
- Pursuit results stored in the same standard format as handicap results

### Series scoring

- Combine multiple races into overall standings
- Automatic scoring from finishing position
- Discard handling
- DNC, DNF, DNS and RET display
- Persistent competitor matching using CompetitorID

### Race result archive

Working/intermediate files are stored in:

    output/

Completed race results are copied to:

    results/

Archived results use descriptive filenames such as:

    Race2_HAND_01112026_results.xlsx
    Race3_PURS_01112026_results.xlsx

This allows the `output/` directory to be reused without overwriting
the permanent historical results.

### OCR / AI digitisation

The original OCR workflow remains part of the project.

- Qwen2.5VL 3B running locally through Ollama
- Full-sheet identity extraction
- Sail-number-led competitor matching
- Lap transcription
- Reference-table correction
- Validation workbook generation

OCR development is currently secondary to the manual race-entry workflow.

## Workflow

The principal workflow is run with:

    python src/run_workflow.py

The workflow coordinates:

1. Race selection
2. Race type selection (HANDICAP or PURSUIT)
3. Race date
4. Manual or OCR entry
5. Validation
6. Race workbook generation
7. Handicap or pursuit result processing
8. Permanent result archiving
9. Series scoring

## Reference data

Competitors are stored in:

    data/reference/sailors.csv

with the structure:

    CompetitorID,Class,Sail No,Helm Name,Crew Name

`CompetitorID` provides a persistent identity independent of changes
to sail number, boat class or competitor details.

## Status

v0.2 represents the first substantially complete race-management
workflow.

Tested:

- Manual handicap race entry
- Validation workflow
- CompetitorID handling
- UPDATE_SAILOR for existing competitors
- Addition of new competitors
- Handicap result calculation
- DNF/DNS/RET scoring and display
- Series standings
- Historical result archiving

The OCR and Pursuit workflows remain areas for further testing
and development.
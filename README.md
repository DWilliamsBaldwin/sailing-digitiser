# Sailing Digitiser

A local workflow for digitising, validating, processing and scoring
sailing race results.

## Current version

v0.3

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

- Compile series automatically from archived race-result workbooks
- Filter races by race type (`HAND` or `PURS`) and user-defined date range
- Multiple races on the same day are treated as separate races
- By-boat scoring using persistent `CompetitorID` values
- Automatic low-point scoring from finishing positions
- DNC scoring using series fleet size + 1
- DNC, DNF, DNS and RET display in individual race results
- Standard discard profile of one discard per three races, with manual override
- Discarded results shown in brackets
- Total and Net series scores
- Excel series output retaining `CompetitorID` for provenance
- Public HTML standings with internal `CompetitorID` hidden
- WFSC-branded HTML output


### Race result archive

Working/intermediate files are stored in:

    output/

Completed race results are copied to:

    results/

Compiled series standings are written to:

    results/Series/

Series output includes both an Excel workbook and a public-facing HTML
standings page.

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
9. Series compilation and scoring
10. Excel and HTML series standings generation

## Reference data

Competitors are stored in:

    data/reference/sailors.csv

with the structure:

    CompetitorID,Class,Sail No,Helm Name,Crew Name

`CompetitorID` provides a persistent identity independent of changes
to sail number, boat class or competitor details.

## Status

v0.3 adds automatic multi-race series compilation to the substantially
complete race-management workflow introduced in v0.2.

Tested:

- Manual handicap race entry
- Validation workflow
- CompetitorID handling
- UPDATE_SAILOR for existing competitors
- Addition of new competitors
- Handicap result calculation
- DNF/DNS/RET scoring and display
- Historical result archiving
- Automatic discovery of archived races for series scoring
- Race-type and date-range filtering
- By-boat series compilation using CompetitorID
- Automatic and manually overridden discard profiles
- DNC series scoring
- Display of discarded race results
- Total and Net series score calculation
- Excel series standings generation
- Public HTML series standings generation
- WFSC-branded HTML output

The initial Winter Series implementation has been independently
cross-checked against Sailwave and produces matching series scores for
the current three-race test series.

Current limitations and planned development:

- By-sailor series scoring is not yet implemented
- Series countback handling requires further validation and
  generalisation
- Multiple-discard presentation requires testing with longer series
- HTML series presentation will continue to be refined
- Pursuit workflows require further testing
- OCR development currently remains secondary to the manual
  race-entry workflow
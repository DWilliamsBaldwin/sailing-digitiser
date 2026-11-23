#!/usr/bin/env python3

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__)
        .resolve()
        .parents[1]
        / "src"
    ),
)

from run_workflow import build_pursuit_results

from series_compiler import (
    apply_series_dnc,
    calculate_series_net_score,
    build_first_metadata,
    build_tiebreak_key,
    discover_series_files,
    get_discard_count,
    get_discard_indices,
    load_all_races,
    merge_n_races,
)


passed = 0
failed = 0


def check(
    name,
    condition,
):

    global passed
    global failed

    if condition:
        print(
            f"PASS: {name}"
        )
        passed += 1

    else:
        print(
            f"FAIL: {name}"
        )
        failed += 1


#
# Standard discard profile
#

check(
    "4 races -> 1 discard",
    get_discard_count(4) == 1,
)

check(
    "10 races -> 3 discards",
    get_discard_count(10) == 3,
)


#
# A8.1
#
# Same net score:
#
# A counted = 1,2,9 = 12
# B counted = 3,3,6 = 12
#
# A must rank ahead because its best
# counted result is better.
#

a81_a = build_tiebreak_key(
    [1, 2, 9, 9],
    1,
)

a81_b = build_tiebreak_key(
    [9, 6, 3, 3],
    1,
)

check(
    "A8.1 counted-score tie-break",
    a81_a < a81_b,
)


#
# A8.2
#
# Both counted sets are:
#
# 1,2,3
#
# so A8.1 cannot separate them.
#
# Last race:
#
# A = 6
# B = 7
#
# A must rank ahead.
#

a82_a = build_tiebreak_key(
    [1, 2, 3, 6],
    1,
)

a82_b = build_tiebreak_key(
    [1, 2, 3, 7],
    1,
)

check(
    "A8.2 last-race comparison",
    a82_a < a82_b,
)


#
# A8.2 backwards comparison.
#
# Counted sets are identical.
# Last race is also identical.
#
# Comparison therefore moves backwards.
# Race 3 is A=4 and B=2, so B ranks ahead.
#

back_a = build_tiebreak_key(
    [1, 2, 4, 3],
    1,
)

back_b = build_tiebreak_key(
    [1, 4, 2, 3],
    1,
)

check(
    "A8.2 backwards comparison",
    back_b < back_a,
)


#
# Ten-race discovery and numeric ordering.
#

from datetime import date

fixture_dir = (
    Path(__file__)
    .resolve()
    .parent
    / "fixtures"
    / "series"
)

discovered = discover_series_files(
    "PURS",
    date(2099, 12, 31),
    date(2099, 12, 31),
    results_dir=fixture_dir,
)

expected_names = [
    f"Race{race_number}_PURS_31122099_results.xlsx"
    for race_number in range(1, 11)
]

discovered_names = [
    path.name
    for path in discovered
]

check(
    "10 synthetic races discovered",
    len(discovered_names) == 10,
)

check(
    "Race1 through Race10 numeric ordering",
    discovered_names == expected_names,
)


#
# Ten-race merge regression.
#
# This specifically protects against the pandas
# suffix collision that previously appeared when
# merging Race 4.
#

boat_races = load_all_races(
    discovered,
    "boat",
)

boat_merged = merge_n_races(
    boat_races,
    "boat",
)

expected_position_columns = [
    f"race_{race_number}_pos"
    for race_number in range(1, 11)
]

boat_position_columns = [
    column
    for column in boat_merged.columns
    if column.startswith("race_")
    and column.endswith("_pos")
]

check(
    "10 races merge successfully in boat mode",
    boat_position_columns
    == expected_position_columns,
)

check(
    "boat merge retains two competitors",
    len(boat_merged) == 2,
)


#
# Helm-mode merge of the same ten races.
#

helm_races = load_all_races(
    discovered,
    "helm",
)

helm_merged = merge_n_races(
    helm_races,
    "helm",
)

helm_position_columns = [
    column
    for column in helm_merged.columns
    if column.startswith("race_")
    and column.endswith("_pos")
]

check(
    "10 races merge successfully in helm mode",
    helm_position_columns
    == expected_position_columns,
)

check(
    "helm merge retains two helms",
    len(helm_merged) == 2,
)


#
# Identity aggregation regression tests.
#

identity_dir = (
    Path(__file__)
    .resolve()
    .parent
    / "fixtures"
    / "identity"
)

identity_files = discover_series_files(
    "PURS",
    date(2099, 12, 30),
    date(2099, 12, 30),
    results_dir=identity_dir,
)

check(
    "3 identity fixture races discovered",
    len(identity_files) == 3,
)


#
# BOAT MODE
#
# Expected unique boats:
#
# COMET 3003
# SUPERNOVA 4004
# GP14 5005
#

identity_boat_races = load_all_races(
    identity_files,
    "boat",
)

identity_boat_merged = merge_n_races(
    identity_boat_races,
    "boat",
)

check(
    "boat mode separates one helm's different boats",
    len(identity_boat_merged) == 3,
)


#
# GP14 5005 is sailed by Test Helm D in races
# 1 and 3, and Test Helm E in race 2.
#
# Boat mode must nevertheless produce ONE boat entry.
#

gp14_boat_rows = identity_boat_merged[
    identity_boat_merged[
        "competitor_id"
    ] == "BOAT5005"
]

check(
    "boat mode combines multiple helms on same boat",
    len(gp14_boat_rows) == 1,
)


#
# HELM MODE
#
# Expected unique helms:
#
# Test Helm C
# Test Helm D
# Test Helm E
#

identity_helm_races = load_all_races(
    identity_files,
    "helm",
)

identity_helm_merged = merge_n_races(
    identity_helm_races,
    "helm",
)

check(
    "helm mode combines one helm across different boats",
    len(
        identity_helm_merged[
            identity_helm_merged[
                "helm_key"
            ] == "test helm c"
        ]
    ) == 1,
)

check(
    "helm mode separates different helms on same boat",
    (
        "test helm d"
        in identity_helm_merged[
            "helm_key"
        ].tolist()
        and
        "test helm e"
        in identity_helm_merged[
            "helm_key"
        ].tolist()
    ),
)


#
# First-sailed metadata for Test Helm C must
# remain COMET 3003 even though that helm sails
# SUPERNOVA 4004 in Race 2.
#

identity_metadata = build_first_metadata(
    identity_helm_races,
    "helm",
)

check(
    "helm metadata keeps first-sailed boat",
    (
        identity_metadata.loc[
            "test helm c",
            "boat_type",
        ] == "COMET"
        and
        str(
            identity_metadata.loc[
                "test helm c",
                "sail_number",
            ]
        ) == "3003"
    ),
)


#
# DNC regression.
#
# The identity fixture has three unique boats.
# BOAT4004 only sails Race 2, so its missing
# Race 1 and Race 3 scores must both become 4.
#

identity_position_cols = [
    f"race_{race_number}_pos"
    for race_number in range(1, 4)
]

dnc_boat_merged, dnc_fleet_size, dnc_score = (
    apply_series_dnc(
        identity_boat_merged,
        identity_position_cols,
    )
)

check(
    "boat-mode DNC fleet size is three",
    dnc_fleet_size == 3,
)

check(
    "boat-mode DNC score is fleet plus one",
    dnc_score == 4,
)

boat_4004 = dnc_boat_merged[
    dnc_boat_merged[
        "competitor_id"
    ] == "BOAT4004"
].iloc[0]

check(
    "absent boat receives DNC in missing races",
    (
        int(boat_4004["race_1_pos"]) == 4
        and
        int(boat_4004["race_2_pos"]) == 1
        and
        int(boat_4004["race_3_pos"]) == 4
    ),
)


#
# Pursuit status regression:
# DNF / DNS / RET must each receive fleet+1,
# while preserving their individual status labels.
#

status_dir = (
    Path(__file__)
    .resolve()
    .parent
    / "fixtures"
    / "status"
)

status_input = (
    status_dir
    / "pursuit_status_input.xlsx"
)

status_output = (
    status_dir
    / "pursuit_status_results.xlsx"
)

if status_output.exists():
    status_output.unlink()

build_pursuit_results(
    status_input,
    status_output,
)

status_df = pd.read_excel(
    status_output
)

status_by_sail = status_df.set_index(
    status_df[
        "sail_number"
    ].astype(str)
)

check(
    "DNF receives pursuit fleet-plus-one score",
    (
        int(
            status_by_sail.loc[
                "6002",
                "corrected_position",
            ]
        ) == 5
        and
        status_by_sail.loc[
            "6002",
            "race_status",
        ] == "DNF"
    ),
)

check(
    "DNS receives pursuit fleet-plus-one score",
    (
        int(
            status_by_sail.loc[
                "6003",
                "corrected_position",
            ]
        ) == 5
        and
        status_by_sail.loc[
            "6003",
            "race_status",
        ] == "DNS"
    ),
)

check(
    "RET receives pursuit fleet-plus-one score",
    (
        int(
            status_by_sail.loc[
                "6004",
                "corrected_position",
            ]
        ) == 5
        and
        status_by_sail.loc[
            "6004",
            "race_status",
        ] == "RET"
    ),
)

check(
    "normal pursuit finisher keeps finishing position",
    int(
        status_by_sail.loc[
            "6001",
            "corrected_position",
        ]
    ) == 1,
)


#
# Multiple-discard regression.
#
# For scores 1..10 and three discards:
#
# gross = 55
# worst three = 10 + 9 + 8 = 27
# net = 28
#

ordered_ten_scores = [
    1, 2, 3, 4, 5,
    6, 7, 8, 9, 10,
]

check(
    "10-race net score discards three worst results",
    calculate_series_net_score(
        ordered_ten_scores,
        3,
    ) == 28,
)


#
# The result must not depend on where the bad
# scores occur chronologically.
#

scrambled_ten_scores = [
    4, 10, 1, 8, 2,
    9, 3, 7, 5, 6,
]

check(
    "multiple discards use worst scores, not latest races",
    calculate_series_net_score(
        scrambled_ten_scores,
        3,
    ) == 28,
)


#
# Zero-discard behaviour should remain sensible.
#

check(
    "zero discards retains gross score",
    calculate_series_net_score(
        [1, 2, 3, 4],
        0,
    ) == 10,
)


#
# Multiple-discard index regression.
#

discard_test_scores = [
    4, 10, 1, 8, 2,
    9, 3, 7, 5, 6,
]

discard_test_indices = get_discard_indices(
    discard_test_scores,
    3,
)

check(
    "three worst race indices are selected",
    set(discard_test_indices)
    == {1, 3, 5},
)

check(
    "selected discard scores are 10, 9 and 8",
    sorted(
        [
            discard_test_scores[index]
            for index in discard_test_indices
        ],
        reverse=True,
    ) == [10, 9, 8],
)

check(
    "zero discards selects no race indices",
    get_discard_indices(
        [1, 2, 3],
        0,
    ) == [],
)


#
# Final summary
#

print()
print(
    f"{passed} tests passed"
)

if failed:

    print(
        f"{failed} tests FAILED"
    )

    raise SystemExit(1)

print(
    "All scoring tests passed."
)

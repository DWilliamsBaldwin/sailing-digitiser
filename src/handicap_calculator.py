import pandas as pd

def calculate_handicap(race_excel_path, py_csv_path, output_path=None):
    # Read race sheet
    df = pd.read_excel(race_excel_path, engine='openpyxl')

    # Compute maximum laps sailed (used for normalization)
    max_laps = df['total_laps'].max()

    # Compute average lap time
    # elapsed_time is expected to be Pandas Timedelta (hh:mm:ss or Excel duration)
    df['average_lap_time'] = df['elapsed_time'] / df['total_laps']

    # Compute adjusted elapsed time for normalization to max laps
    # Default adjusted elapsed = average_lap_time * max_laps
    df['adjusted_elapsed_time'] = df['average_lap_time'] * max_laps
    # For those who sailed the maximum laps, adjusted_elapsed_time should equal elapsed_time
    mask_max = df['total_laps'] == max_laps
    df.loc[mask_max, 'adjusted_elapsed_time'] = df.loc[mask_max, 'elapsed_time']

    # Read PY lookup values
    py_df = pd.read_csv(py_csv_path)
    # Merge PY values on boat_type
    df = df.merge(py_df, on='boat_type', how='left')

    # Calculate corrected time: standard RYA sum-of-laps method
    # corrected_time = adjusted_elapsed_time * 1000 / PY
    df['corrected_time'] = df['adjusted_elapsed_time'] * 1000 / df['py']

    # Rank competitors by corrected_time (lower is better)
    df['corrected_position'] = df['corrected_time'].rank(method='min', ascending=True).astype(int)

    # Sort by corrected_time to produce leaderboard
    df.sort_values('corrected_time', inplace=True)
    # Reset index if desired
    df.reset_index(drop=True, inplace=True)

    # Optionally write results to Excel or CSV
    if output_path:
        # Use excel or csv extension
        if output_path.lower().endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Calculate handicap corrected times for a race sheet.')
    parser.add_argument('--race', default='race1.xlsx', help='Path to race workbook (Excel file).')
    parser.add_argument('--py', default='py_lookup.csv', help='Path to PY lookup CSV file.')
    parser.add_argument('--output', default='race1_results.xlsx', help='Output file path (Excel or CSV).')
    args = parser.parse_args()
    results = calculate_handicap(args.race, args.py, args.output)
    results.reset_index(drop=True,inplace=True)
    results.index = results.index + 1

    # Print out key fields for verification

    print(results[['boat_type','sail_number','helm','crew','elapsed_time','total_laps','py','corrected_time','corrected_position']])

"""Reshape the per-window CSV from `analyze.py` onto a unified frequency grid.

The raw output from `analyze.py` lists, for each window, an arbitrary set of
peak frequencies in `Freq_1..Freq_N` and their amplitudes in `Amp_1..Amp_N`.
Across windows the same physical harmonic can land in different columns
(e.g. column 3 in one row, column 4 in the next) because peak ordering by
magnitude shifts as the note decays.

This module collects every distinct frequency seen across all windows and
re-emits the data with one column per frequency, leaving cells blank where
that frequency was not among the top peaks for that window. The reshaped
file is what gets fed into the per-harmonic exponential fits.
"""

import csv
import os


def cleanup_modal_csv(input_csv):
    """Read the analyze.py CSV and write a `<basename>_clean.csv` next to it."""
    base, _ = os.path.splitext(input_csv)
    output_csv = base + "_clean.csv"

    with open(input_csv, newline="") as f:
        reader = list(csv.reader(f))

    header = reader[0]
    # Header layout: Time, Amp_1..Amp_N, Freq_1..Freq_N
    num_modes = (len(header) - 1) // 2

    # Step 1: collect every distinct peak frequency across all rows
    all_freqs = set()
    data_by_time = []

    for row in reader[1:]:
        time = row[0]
        amps = row[1:1 + num_modes]
        freqs = row[1 + num_modes:]
        freq_amp_map = {float(freq): amp for amp, freq in zip(amps, freqs)}
        all_freqs.update(freq_amp_map.keys())
        data_by_time.append((time, freq_amp_map))

    # Step 2: define a stable column order
    sorted_freqs = sorted(all_freqs)

    # Step 3: emit a wide CSV — one column per frequency, blanks where missing
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time (s)"] + [f"{freq:.3f}" for freq in sorted_freqs])

        for time, freq_amp_map in data_by_time:
            row = [time]
            for freq in sorted_freqs:
                row.append(freq_amp_map.get(freq, ""))
            writer.writerow(row)

    print(f"Saved cleaned CSV to: {output_csv}")


if __name__ == "__main__":
    cleanup_modal_csv("Piano_C5.csv")

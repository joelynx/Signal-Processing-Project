"""Windowed-FFT analysis of an instrument recording.

Slides a Hann-windowed FFT across a .wav file and, for each window, extracts
the `num_modes` strongest spectral peaks within a frequency band. The output
CSV has one row per window center time, with columns for the amplitude and
frequency of each peak.

The intent is to track how the amplitude of each harmonic evolves as the note
decays. Window length should be an integer number of fundamental cycles (the
default 76.4 ms is ~10 cycles of C3 at 130.81 Hz) so each window captures
whole oscillations of every harmonic and resolves them cleanly in frequency.
"""

import csv
import os

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal
from scipy.fft import fft


def get_dominant_peaks(signal_segment, fs, num_modes=18, min_freq=100, max_freq=6000):
    """Return the top `num_modes` spectral peaks in `signal_segment`.

    Applies a Hann window to suppress spectral leakage from the discontinuity
    at the segment edges, takes the magnitude FFT, restricts to [min_freq,
    max_freq], picks local maxima, and returns the strongest `num_modes` of
    them sorted ascending by frequency.
    """
    N = len(signal_segment)
    windowed = signal_segment * np.hanning(N)
    spectrum = np.abs(fft(windowed))[:N // 2]
    freqs = np.fft.fftfreq(N, d=1 / fs)[:N // 2]

    # Restrict to the frequency band of interest
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    spectrum = spectrum[mask]
    freqs = freqs[mask]

    # All local maxima in the band
    peak_indices, _ = scipy.signal.find_peaks(spectrum, distance=5)
    peak_mags = spectrum[peak_indices]
    peak_freqs = freqs[peak_indices]

    # Take top N peaks (descending magnitude), then re-sort by frequency
    top_indices = np.argsort(peak_mags)[-num_modes:][::-1]
    top_freqs = peak_freqs[top_indices]
    top_amps = peak_mags[top_indices]

    sort_order = np.argsort(top_freqs)
    return top_amps[sort_order], top_freqs[sort_order]


def analyze_wav(file_path, num_modes=18, window_length_sec=0.07644675,
                hop_fraction=0.25, output_csv=None):
    """Run windowed-FFT peak extraction across an entire .wav file.

    Parameters
    ----------
    file_path : str
        Path to the input .wav file.
    num_modes : int
        Number of spectral peaks to track per window.
    window_length_sec : float
        Window duration in seconds. Should be an integer multiple of the
        fundamental's period (default ≈ 10 cycles of C3).
    hop_fraction : float
        Hop size as a fraction of window length (0.25 → 75% overlap).
    output_csv : str or None
        Output path. If None, derived from the input file's parent folder
        name + base name (e.g. `Nylon/C3.wav` → `Nylon_C3.csv`).
    """
    fs, signal = wav.read(file_path)

    if output_csv is None:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        folder_name = os.path.basename(os.path.dirname(file_path))
        output_csv = f"{folder_name}_{base_name}.csv"

    # Stereo → mono by averaging channels
    if signal.ndim > 1:
        signal = signal.mean(axis=1)

    # Normalize to [-1, 1] so peak magnitudes are comparable across files
    signal = signal / np.max(np.abs(signal))

    window_length = int(fs * window_length_sec)
    hop_size = int(window_length * hop_fraction)

    results = []
    for start in range(0, len(signal) - window_length, hop_size):
        segment = signal[start:start + window_length]
        # Tag each window with the time of its center
        center_time = (start + window_length // 2) / fs

        amps, freqs = get_dominant_peaks(segment, fs, num_modes)
        row = [center_time] + list(amps) + list(freqs)
        results.append(row)

    amp_headers = [f"Amp_{i+1}" for i in range(num_modes)]
    freq_headers = [f"Freq_{i+1}" for i in range(num_modes)]
    header = ["Time (s)"] + amp_headers + freq_headers

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)

    print(f"Saved modal analysis to: {os.path.abspath(output_csv)}")


if __name__ == "__main__":
    # Example: place a recording at data/recordings/Nylon/C3.wav and run.
    analyze_wav("data/recordings/Nylon/C3.wav")

"""Additive synthesis: rebuild a tone from fitted harmonic parameters.

Given a list of (amplitude, decay rate, frequency, phase) tuples — one per
harmonic, fitted externally from the windowed-FFT output — this script sums
decaying sinusoids into a single signal and writes it as a 16-bit .wav file:

    S(t) = sum_i  A_i * exp(-k_i * t) * sin(2 * pi * f_i * t + phi_i)

If the fit captures the physics of the original recording, the synthesized
audio should be perceptually close to the original instrument's note.

The example parameters below correspond to B3 on the nylon-string guitar
analyzed in the report (fundamental f1 ≈ 220 Hz, 18 harmonics, phases set to
zero — see the report for why phase is intentionally ignored).
"""

import numpy as np
from scipy.io.wavfile import write


sample_rate = 44100
duration = 5.0  # seconds

t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Fundamental frequency (Hz). Harmonics are integer multiples below.
r = 220

# (A, k, f, phi) per harmonic — amplitude, decay rate, frequency, phase.
expsines = [
    (249.00129, 2.63227,   1 * r, 0), (128.59441, 2.38308,  2 * r, 0),
    (6.66523,   2.62981,   3 * r, 0), (46.60635,  2.99151,  4 * r, 0),
    (10.64565,  3.40945,   5 * r, 0), (4.93575,   4.72225,  6 * r, 0),
    (9.51669,   3.38721,   7 * r, 0), (4.299,     5.31225,  8 * r, 0),
    (8.53218,   13.66037,  9 * r, 0), (2.57448,   4.15758,  10 * r, 0),
    (6.25496,   7.56688,   11 * r, 0), (1.79722,  4.68457,  12 * r, 0),
    (1.19145,   4.77753,   13 * r, 0), (1.94734,  4.28449,  14 * r, 0),
    (1.83891,   6.76555,   15 * r, 0), (1.87871,  7.54312,  16 * r, 0),
    (5.1243,    13.04117,  17 * r, 0), (6.23217,  17.61705, 18 * r, 0),
]

# Sum the decaying sinusoids
signal = np.zeros_like(t)
for A, k, f, phi in expsines:
    signal += A * np.exp(-k * t) * np.sin(2 * np.pi * f * t + phi)

# Normalize and convert to 16-bit PCM
signal /= np.max(np.abs(signal))
signal = (signal * 32767).astype(np.int16)

write("expsines.wav", sample_rate, signal)

# Signal Processing of Musical Instruments

Decomposing the timbre of plucked-string instruments into a sum of decaying harmonics, then validating the model by re-synthesizing the recording from its fitted parameters.

Originally a lab project for AELP101 at IIT-Delhi Abu Dhabi (Sem 2, 2024–25). The full write-up — derivations, tables, and reconstruction audio links — lives in [`Report.pdf`](Report.pdf).

## What it does

Two instruments playing the same fundamental frequency don't sound the same. The difference is *timbre*: the relative strength and decay rate of the overtones above the fundamental. This project quantifies timbre for a recorded note in three steps:

1. **Analyze** — slide a Hann-windowed FFT across the recording, and for each window extract the 18 strongest spectral peaks. This gives a time series of amplitude vs. time for each harmonic as the note decays.
2. **Fit** — for each harmonic, fit an exponential decay `A·exp(-k·t)` to its amplitude time series.
3. **Synthesize** — sum decaying sinusoids using the fitted `(A, k, f)` per harmonic, write to .wav, listen. If the model captures the physics, the reconstruction sounds like the original instrument.

Tested on a nylon-string guitar (B3) and a piano (B4); reconstructions are recognizable as the source instrument. See the report for full numerical results.

## Background

### The decay model

A struck or plucked string oscillates in a superposition of standing-wave modes — a fundamental plus integer-multiple overtones (the *harmonic* assumption, valid for strings since the wave equation is linear and non-dispersive). Each mode loses energy roughly linearly in its oscillation velocity (elastic hysteresis, air drag, coupling into the resonator body), which gives an exponential decay envelope. Modeling each harmonic individually:

```
S_i(t) = A_i · exp(-k_i · t) · sin(2π f_i t + φ_i),     f_i = i · f_1
```

The full signal is the sum over `i = 1..18`. The free parameters `(A_i, k_i)` are what we want to extract from the recording. Phase `φ_i` is set to zero throughout — the human ear is largely insensitive to harmonic phase relationships, and they vary with pluck position anyway.

### Windowed FFT

A plain FFT on the whole recording would tell us which frequencies are present, but not how their amplitudes evolve — the signal isn't stationary. The fix:

- Chop the signal into short windows where amplitude is approximately constant.
- Multiply each window by a Hann taper (suppresses spectral leakage from the discontinuities at the window edges).
- FFT each window, take the magnitude spectrum, and pick the strongest peaks within the band of interest.
- Plot peak amplitude vs. window center time → the decay envelope of each harmonic.

Window length is chosen as ~10–15 fundamental periods: long enough for clean frequency resolution, short enough to localize in time. Successive windows overlap by 75% (`hop_fraction = 0.25`) so the time evolution is smooth.

### Validation

Fitting `A·exp(-k·t)` to each harmonic's time series gives one `(A, k)` pair per harmonic. Plug these and the integer-multiple frequencies into the model, render to audio, compare. The reconstruction won't perfectly match the original — the model has no body resonance, no nonlinearities, no inharmonicity — but if it sounds like the same instrument, the dominant physics is captured.

## Project structure

```
.
├── README.md
├── Report.pdf            Full write-up: theory, derivations, results, audio links
├── Report.tex            LaTeX source
├── requirements.txt
├── .gitignore
├── src/
│   ├── analyze.py        Windowed FFT → CSV of peak amplitudes & frequencies vs. time
│   ├── cleanup.py        Reshape CSV onto a unified frequency grid (one column per harmonic)
│   └── synthesize.py     Additive synthesis from fitted (A, k, f, φ) parameters → .wav
└── data/
    └── recordings/       Place input .wav files here (gitignored)
```

## How to run it

```bash
pip install -r requirements.txt
```

The pipeline is three stages, run in order:

```bash
# 1. Record a single note (~5s including the decay tail). Place it at e.g.
#    data/recordings/Nylon/C3.wav. Mono or stereo, any sample rate.

# 2. Run the windowed FFT. Edit the call at the bottom of analyze.py to point
#    at your file, then:
python src/analyze.py
# → writes Nylon_C3.csv (amps & freqs per window)

# 3. Reshape onto a unified frequency grid:
python src/cleanup.py
# → writes Nylon_C3_clean.csv

# 4. Externally (Desmos, scipy.optimize, etc.) fit A·exp(-k·t) to each harmonic
#    column. Paste the resulting (A, k, f, φ) tuples into the `expsines` list in
#    synthesize.py, then:
python src/synthesize.py
# → writes expsines.wav — the reconstructed signal
```

### Tunable parameters (`analyze.py`)

| Parameter           | What it controls                                                             |
|---------------------|------------------------------------------------------------------------------|
| `num_modes`         | Number of harmonics tracked (default 18).                                    |
| `min_freq`/`max_freq` | Frequency band searched for peaks (default 100–6000 Hz).                   |
| `window_length_sec` | Window duration. Set to an integer multiple of the fundamental's period.    |
| `hop_fraction`      | Hop as a fraction of window length. 0.25 → 75% overlap.                      |

For correct windowing, ensure `window_length_sec × f_fundamental` is a whole number (window covers complete cycles) and `hop_fraction × cycles_per_window` is also a whole number (windows align with cycle boundaries).

## Results

For B3 on a nylon-string guitar (`f₁ = 246.94 Hz`, 18 harmonics tracked), amplitudes follow a roughly `1/n²` envelope — consistent with the theoretical pluck-position formula derived in the report — and decay rates broadly increase with harmonic number. Reconstructed audio is clearly recognizable as the same instrument. For B4 on a piano (`f₁ = 493.88 Hz`), the first 11 harmonics dominate; reconstruction is similarly faithful. Numerical tables and links to the actual `.wav` reconstructions are in [`Report.pdf`](Report.pdf).

## Limitations

- Hand-off between `cleanup.py` and `synthesize.py` is manual — fitting `A·exp(-k·t)` to each harmonic was done in Desmos for the original report. Automating with `scipy.optimize.curve_fit` would be a natural extension.
- The model is decaying-sinusoid-only: no body resonance, no inharmonicity, no slight detuning between harmonics. Works well for guitar/piano; would fail for inharmonic instruments like kalimbas or bells.
- Phase is fixed at zero. Audible only on careful comparison — see the report's *Phase Considerations* section for the rationale.

## Authors

Joel Jobi, Karthik Nambiar — IIT-Delhi Abu Dhabi, AELP101 (Sem 2, 2024–25).

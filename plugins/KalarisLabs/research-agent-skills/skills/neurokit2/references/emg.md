# Electromyography

Checked **2026-07-23** against NeuroKit2 0.2.13 stable runtime/source,
the official EMG API, and human surface-EMG guidance.

## Acquisition contract

Record muscle and task, electrode type/size/orientation/inter-electrode distance,
reference, skin preparation, amplifier gain/range, hardware filters, unit, sampling
rate, synchronization, posture/contraction, and artifact annotations. Follow a
muscle-specific placement protocol such as SENIAM when applicable.

EMG amplitude depends on geometry, subcutaneous tissue, cross-talk, electrode contact,
hardware, and contraction history. It is not a direct universal force scale.

## Stable processing pipeline

```python
signals, info = nk.emg_process(emg, sampling_rate=1000)
```

Pinned 0.2.13 default columns:

```text
EMG_Raw, EMG_Clean, EMG_Amplitude,
EMG_Activity, EMG_Onsets, EMG_Offsets
```

`info` contained event-level `EMG_Activity`, `EMG_Onsets`, `EMG_Offsets`, and
`sampling_rate`. This is a default observation, not a universal schema.

## Cleaning and amplitude

```python
clean = nk.emg_clean(emg, sampling_rate=1000, method="biosppy")
amplitude = nk.emg_amplitude(clean)
```

Important stable details:

- `emg_clean()` currently offers `biosppy` and `none`.
- The BioSPPy path uses a fourth-order 100 Hz high-pass Butterworth filter followed by
  constant detrending.
- `emg_amplitude()` takes only the cleaned vector; it has no `sampling_rate` argument
  in 0.2.13.

A 100 Hz high-pass may be unsuitable for some surface-EMG endpoints and impossible at
low sampling rates. Do not treat the package default as a universal acquisition
standard. Set sampling rate above twice the highest retained frequency with transition
band margin; surface EMG is commonly acquired around 1000–2000 Hz, but the study,
hardware, muscle, and endpoint determine requirements.

## Activation detection

Stable signature:

```text
emg_activation(
  emg_amplitude=None, emg_cleaned=None, sampling_rate=1000,
  method="threshold", threshold="default", duration_min="default",
  size=None, threshold_size=None, **kwargs
)
```

Use the correct input for the method:

- `threshold` or `mixture`: pass `emg_amplitude`;
- `pelt`, `biosppy`, or `silva`: pass `emg_cleaned`.

```python
activity_signals, activity_info = nk.emg_activation(
    emg_amplitude=amplitude,
    sampling_rate=1000,
    method="threshold",
    threshold="default",
    duration_min=0.05,
)
```

Return order is `(activity_signals, info)`. The DataFrame has same-length
`EMG_Activity`, `EMG_Onsets`, and `EMG_Offsets`; the dict contains event indices.
`duration_min` is seconds. `size` semantics are method-specific.

Automatic thresholds are hypotheses, not ground truth. Tune/validate on independent
labeled contractions or a prespecified baseline. Report threshold, window, smoothing,
minimum duration, and false/missed activation performance.

## Missing data and artifacts

Inspect and annotate:

- clipping/saturation and disconnected/flat channels;
- motion/cable artifacts and low-frequency transients;
- powerline interference;
- ECG contamination, especially trunk/proximal sites;
- cross-talk from adjacent muscles; and
- baseline changes from contact/sweat.

Do not interpolate across a burst or activation onset. Segment long gaps, preserve a
validity mask, and reject affected trials/windows under prespecified rules. Filtering
cannot establish that a deflection came from the target muscle.

## Event and interval features

```python
epochs = nk.epochs_create(
    signals,
    events,
    sampling_rate=1000,
    epochs_start=-0.1,
    epochs_end=1.0,
    baseline_correction=False,
)
event_features = nk.emg_eventrelated(epochs)
interval_features = nk.emg_intervalrelated(signals)
```

Documented event-related features include `EMG_Activation`,
`EMG_Amplitude_Mean`, `EMG_Amplitude_Max`, `EMG_Amplitude_SD`,
`EMG_Amplitude_Max_Time`, and `EMG_Bursts`. Interval analysis returns
`EMG_Activation_N` and `EMG_Amplitude_Mean` in the pinned official example.
Columns are conditional; inspect output.

For startle or rapid onset work, hardware latency, synchronization, filter group delay,
rectification/smoothing, and onset-definition error can dominate the result.

## Normalization

Raw/envelope amplitude is usually not comparable across participants or sessions.
Possible denominators include MVC, reference contraction, or within-participant
standardization, but each changes the estimand.

If using MVC:

- acquire it with a validated, safe protocol;
- inspect fatigue, pain, effort, clipping, and target/cross-talk;
- define which statistic and window represent MVC;
- report repetitions and reliability; and
- never divide by a near-zero/invalid reference.

Normalization does not make electrode/site differences disappear.

## Interpretation boundary

NeuroKit2 EMG can support research on amplitude and detected activity. It does not
provide validated motor-unit decomposition, neuromuscular diagnosis, fatigue
monitoring, prosthetic control safety, rehabilitation decisions, or sleep scoring.
Those require endpoint-specific acquisition, algorithms, standards, and independent
validation.

## Sources checked 2026-07-23

- [Official EMG API](https://neuropsychology.github.io/NeuroKit/functions/emg.html)
- [Stable v0.2.13 EMG source](https://github.com/neuropsychology/NeuroKit/tree/v0.2.13/neurokit2/emg)
- [Fridlund & Cacioppo (1986), human EMG guidelines](https://pubmed.ncbi.nlm.nih.gov/3809364/)
- [Hermens et al. (2000), SENIAM sensor/placement recommendations](https://doi.org/10.1016/S1050-6411(00)00027-4)
- [Blumenthal et al. (2005), startle eyeblink EMG guidelines](https://doi.org/10.1111/j.1469-8986.2005.00271.x)

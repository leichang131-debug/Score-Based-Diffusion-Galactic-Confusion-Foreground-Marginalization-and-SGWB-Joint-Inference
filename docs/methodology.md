# Scientific workflow

The current baseline uses daily segments of second-generation XYZ TDI data. The time-domain cases simulate and transform the streams to spectral observations. The static equal-arm frequency-domain case generates spectral observations directly. A complex Hermitian three-channel covariance models each retained segment and frequency. Its terms describe acceleration noise, optical metrology noise, an effective isotropic Galactic binary foreground, an astrophysical power law, and sound waves from a phase transition.

A complex Gaussian spectral likelihood uses the XYZ auto- and cross-spectra. The factorization over segments and frequency bins is an approximation. Static detector tables permit an exact sum over observations across segments within that likelihood. The unequal-arm case retains segment-dependent detector tables. Bilby/Dynesty returns marginal posteriors and log evidences. Joint inference propagates uncertainty in foreground and noise parameters to the target background.

Compare each full fit with a no-sound-wave fit on the same input and compare runtime across the three matched detector configurations. Keep data preparation, compilation, sampling, and post-processing measurements distinct. See the [baseline plan](research-plan/full-covariance-baseline.md).

Future work will test detector and foreground mismatch with controlled simulations. Score-based likelihood correction will be evaluated against covariance-matched controls and physically informed foreground models using held-out simulations and posterior calibration.

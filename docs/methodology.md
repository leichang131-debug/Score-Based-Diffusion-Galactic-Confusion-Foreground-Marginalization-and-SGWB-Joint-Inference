# Scientific workflow

## Observation and uncertainty

Analyze a consistent multichannel representation of Galactic foreground, target SGWB, and instrument noise. Preserve the relevant channel, frequency, and epoch correlations. Condition on known detector states and jointly infer unknown physical scales.

## Two marginalizations

At fixed physical parameters, integrate over possible foreground realizations. Conditional training simulations can represent this distribution by repeatedly drawing foreground realizations. The foreground amplitude remains an inference parameter.

After obtaining the joint posterior, integrate over foreground and noise parameters to report the target SGWB posterior. Do not replace these integrations with a single estimated foreground waveform.

## Density interface

Learn conditional scores across artificial diffusion times. Use a probability-flow ODE with a known terminal density and divergence integration to define the flow-model likelihood. Validate endpoint approximation, normalization, standardization Jacobians, and numerical error. The learned density is approximate and requires independent checks.

## Validation

Start with analytically tractable Gaussian, non-Gaussian-mixture, and non-identifiable controls. Establish strong second-order and flexible-foreground baselines. Check inference calibration, bias, false alarms, and detection power at comparable false-alarm rates.

Covariance-matched Gaussian foreground controls can help attribute gains to higher-order information. Test source-population changes, subtraction errors, and detector mismatch before extending claims.

# Repository documentation and evidence maintenance — 2026-10-15

## Scope and outcome

Current entry points and cross-stage summaries were reviewed against the completed reproduction evidence. Outdated current-tense statements were corrected; original upstream source, executed notebook code/Markdown, original execution logs, historical failures, stored samples, checkpoint states and figures were not changed. No training, simulation or MCMC was launched.

The principal current entry points are the root README, `docs/reproduction/README.md`, `results/README.md`, and `docs/reproduction/taiji-sgwb/status-and-cluster-handoff.md`. Source storage is described in `external/README.md`: four top-level submodules remain, while TaijiSGWB is a directly tracked fixed source snapshot. Root directory diagrams now include Triangle-BBH, reproduction/upstream configurations and component result folders.

## Corrected stale statements

- Global initialization-only roadmap/results/script placeholders were updated to the actual implemented local workflows; research implementation and cluster placeholders remain explicitly future work.
- TaijiSGWB environment/data/response/likelihood/short-chain reports no longer say their subsequently completed stages are pending. Full-data template completion is separated from unconfirmed convergence and unexecuted EQ/RJ experiments.
- Earlier burn-108/337 pause and interruption material is explicitly historical, with a link to current status. Historical JSON, PIDs, timestamps, progress and failure records remain unchanged.
- Triangle-GB source-only/result indexes no longer say there are no executed examples or only README placeholders. All five local example runs are linked, alongside the six retained core-check failures and orbit/posterior limits.
- Triangle-Simulator Tutorial 1/2/3 tails now acknowledge subsequent tutorial completion. Tutorial 5 remains excluded.
- The Score-SDE source map now points to completed final plotting/export instead of calling it pending. No 214k training-quality claim was added.

## Evidence integrity

The initial repository-wide scan checked 1083 supported manifest hash entries and found two stale references, both pointing to the current Triangle-GB overview document in environment/prerequisite manifests. There were no missing targets and no broken project-local Markdown links in that scan. `before.json` records these findings. After updating documentation, affected current-file manifests were refreshed only for documented changed project files. `manifest-refresh.json` records each old/new hash and any byte-count update. This refresh does not mean historical scientific checks were rerun; their timestamps, scope, results and known failures are retained.

Eight TaijiSGWB integrity audits were actually rerun: environment 9/9, data 13/13, preprocessing 25/25, response 18/18, likelihood 27/27, short-chain 30/30, mini 42/42 and formal 24/24. These audits check inputs, source/cache identities and saved evidence, not posterior convergence. The new `scripts/reproduction/audit-repository-documentation.py` performs a reproducible read-only tracked-file syntax, local-link, root directory-diagram and supported manifest-hash audit. Its final output is `verification.json`. Remote URL reachability, Markdown anchors, statistical calibration and every possible application branch are outside that audit.

## Mini analyzer lifecycle fix

The historical mini analyzer required the separate full-data run to remain paused. That assumption became obsolete after formal sampling completed. It now records before/after SHA-256 equality of the existing formal status, final artifacts and saved pause checkpoint. This preserves the intended non-interference check for paused or completed runs without treating a lifecycle change as a physics failure.

The pre-fix analyzer is preserved under `results/taiji-sgwb/template-mini/attempts/before-lifecycle-guard-update/analyzer.py`. The updated analyzer was run only with output redirected to ignored `runs/repository-maintenance-20261015/mini-rerender/`. All 11 numerical checks pass. All four mini PNGs are pixel-identical; posterior/diagnostic/sampling values and cold-chain arrays are unchanged. `mini-guard-check.json` records the current analyzer hash and comparisons. Canonical mini analysis JSON, status, PNGs and execution logs retain their original historical content.

## Continuing limitations

Score-SDE image quality at 214k is not reproduced. Triangle-GB core acceptance remains 22/28 with six failures. TaijiSGWB 2.8 template schedule completion does not confirm convergence; 2/14 conservative parameter flags pass. EQ/RJ sampling, independent ensembles, Linux deployment and unknown-foreground diffusion inference remain incomplete. No cluster resources or runtime are assumed.

`updated-documents.json` lists revised documentation. `manifest.json` hashes the maintenance report, audit utility and compact evidence files; `verification.json` is excluded from that manifest to avoid self-referential hashes and is regenerated by the read-only audit.

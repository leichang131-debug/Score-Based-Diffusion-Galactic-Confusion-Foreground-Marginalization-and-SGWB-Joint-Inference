# Route B research and A800 implementation plan

Version 1.0, October 20, 2026. The Chinese-language PDF is for detailed research discussion; repository metadata and navigation remain in English.

- [Read the PDF](route-b-research-and-server-implementation-plan.pdf).
- [Standalone LaTeX source](main.tex).
- [Input provenance](source-provenance.json).
- [Output checksums](manifest.json).
- [Build and visual QA](quality-check.json).

The plan covers the fixed TaijiSGWB baseline, six limitations, corrected sampling/whitening conventions, residual denoising score matching, normalized probability-flow density evaluation, exact Gaussian controls, physical foreground upgrades, posterior calibration, server migration, resource budgets, checkpoint recovery, proposed APIs and evidence requirements. P0-P7 are proposed stages, not implemented software. Numerical thresholds and work-day estimates are planning suggestions, not measured performance.

The pre-plan parent repository and remote main were both `13210dd95af32cdb376d4bcedebeb262334308eb`. Upstream TaijiSGWB HEAD was checked as `4afaad4044b08721e7f1ce29cba3b0d912636dce`. Historical reproduction limitations are preserved: Score-SDE has only 200 updates; Triangle-GB retains six core-check failures; the completed TaijiSGWB template schedule has unconfirmed convergence.

Server access and the resource snapshot are verified, but project deployment, Linux dependencies, GPU-framework execution and background recovery remain to be validated. The plan does not grant exclusive use of shared host memory or all visible CPUs.

## Build

Run `python3 build.py` with XeLaTeX and the packages used in `main.tex`. The source selects Songti/Heiti on macOS and Fandol fonts when available elsewhere. Fonts can change pagination; re-render and inspect a rebuild.

The delivered PDF was built successfully with local XeLaTeX and embedded system CJK fonts. The desktop sandboxed preview compiler could not access those fonts and failed; it is not the build used for the deliverable. Build intermediates and page-render QA remain outside the repository. Use the committed PDF for reliable viewing.

## Source and publication boundaries

The teacher-provided tutorials, Route B PDF and private meeting/architecture images are represented by hashes and an analytical synthesis. Raw private inputs, credentials, SSH addresses, private keys and personal absolute paths are not published. Reported measurements from another environment are explicitly distinguished from local reproduction evidence.

The archived October 7 framework remains unchanged. The new gated inference schedule supersedes its earlier four-scale starting proposal. No scientific run, training or sampling was performed to create this planning document.

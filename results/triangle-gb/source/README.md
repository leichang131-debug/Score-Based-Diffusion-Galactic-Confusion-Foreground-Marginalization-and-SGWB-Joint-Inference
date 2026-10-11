# Source-only audit evidence

`audit.json` checks the pinned checkout, clean source, source-file correspondence to Git objects, required classes, notebook inventory, orbit inputs and license. `manifest.json` lists all upstream tracked files with sizes and SHA-256.

These checks do not execute Triangle-GB, create its development environment or reproduce its examples. The audit script uses only Python standard-library modules and reads source as data.

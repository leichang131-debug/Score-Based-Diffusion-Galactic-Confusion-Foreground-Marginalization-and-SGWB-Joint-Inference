#!/usr/bin/env python3
"""Read-only evidence/source audit; refresh hashes without rerunning sampling."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/environment"


def main():
    report = json.loads((OUT / "check.json").read_text())
    run = json.loads((OUT / "run.json").read_text())
    checks = {}
    checks["all_environment_checks_pass"] = report["all_checks_pass"] and all(v["passed"] for v in report["checks"].values())
    checks["successful_recorded_execution"] = run["success"] and all(c["returncode"] == 0 for c in run["commands"])
    checks["locked_versions_verified"] = run["all_locked_versions_match"] and run["locked_package_count"] == 51
    checks["original_demo_imports_executed"] = all(report["checks"]["original_imports_" + name]["passed"]
        for name in ["template_nofg_28t.py", "rj_nofg_28t.py"])
    checks["synthetic_scope_explicit"] = "synthetic" in report["scope"] and "No TDC dataset" in report["scope"]
    source = ROOT / "external/taiji-sgwb"
    manifest = json.loads((ROOT / "results/taiji-sgwb/source/manifest.json").read_text())
    checks["all_upstream_file_hashes_preserved"] = all(hashlib.sha256((source / f["path"]).read_bytes()).hexdigest() == f["sha256"] for f in manifest["files"])
    checks["upstream_clean"] = not subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]).strip()
    checks["all_checks_in_execution_log"] = all("PASS " + name in (OUT / "execution.txt").read_text() for name in report["checks"])
    first = json.loads((OUT / "first-check.json").read_text())
    checks["first_check_failure_retained"] = not first["all_checks_pass"] and not first["checks"]["original_editable_package"]["passed"]
    result = {"scope": "Evidence integrity and unchanged source only; no repeated interface sampling or posterior validation.",
              "checks": checks, "all_checks_pass": all(checks.values())}
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    artifacts = [p for p in OUT.rglob("*") if p.is_file() and p.name != "manifest.json"]
    artifacts += [ROOT / "environments/taiji-sgwb" / name for name in ["README.md", "requirements.in", "requirements-macos-arm64-py311.txt"]]
    artifacts += [ROOT / "scripts/reproduction" / name for name in ["setup-taiji-sgwb-macos.sh", "check-taiji-sgwb-environment.py", "run-taiji-sgwb-environment-check.py", "run-taiji-sgwb-python.sh", "audit-taiji-sgwb-environment.py", "audit-taiji-sgwb-source.py"]]
    artifacts += [ROOT / "docs/reproduction/taiji-sgwb/environment-setup.md"]
    entries = [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(artifacts)]
    (OUT / "manifest.json").write_text(json.dumps({"schema_version": 1, "files": entries}, indent=2) + "\n")
    print(f"TaijiSGWB environment evidence audit: {sum(checks.values())}/{len(checks)} passed; {len(entries)} hashed artifacts.")
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

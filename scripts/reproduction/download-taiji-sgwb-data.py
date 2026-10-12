#!/usr/bin/env python3
"""Download the official 2.8 training data and pinned orbit with checksums."""
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/taiji-sgwb/data"
RAW = ROOT / "data/raw/taiji-sgwb"
RECORD = "17538642"
SIM_PIN = "ab796358e9a36c8987f6bb53a97230d603bfdfd5"


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            md5.update(block)
            sha.update(block)
    return {"bytes": path.stat().st_size, "md5": md5.hexdigest(), "sha256": sha.hexdigest()}


def curl(url, destination, resume=False):
    command = ["curl", "--fail", "--location", "--retry", "3", "--retry-delay", "2", "--connect-timeout", "30"]
    if resume:
        command += ["--continue-at", "-"]
    command += [url, "--output", str(destination)]
    subprocess.run(command, check=True)


def ranged_download(url, partial, size):
    """Four bounded transfers; verify each Content-Range before assembly."""
    prefix = partial.stat().st_size if partial.exists() else 0
    assert prefix <= size
    folder = ROOT / "runs/taiji-sgwb/data-preparation/ranges"
    folder.mkdir(parents=True, exist_ok=True)
    block = 32 * 1024 * 1024
    ranges = [(start, min(start + block, size) - 1) for start in range(prefix, size, block)]

    def fetch(bounds):
        start, end = bounds
        file = folder / f"{start}-{end}.bin"
        headers = folder / f"{start}-{end}.headers"
        if not (file.exists() and file.stat().st_size == end-start+1 and headers.exists()
                and f"content-range: bytes {start}-{end}/{size}" in headers.read_text().lower()):
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "3", "--retry-all-errors",
                "--retry-delay", "2", "--connect-timeout", "30", "--range", f"{start}-{end}",
                "--max-filesize", str(end-start+1), "--dump-header", str(headers), url, "--output", str(file)], check=True)
        assert file.stat().st_size == end-start+1
        assert f"content-range: bytes {start}-{end}/{size}" in headers.read_text().lower()
        return {"start": start, "end": end, "bytes": file.stat().st_size,
                "sha256": hashes(file)["sha256"], "verified_content_range": True}

    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in as_completed([pool.submit(fetch, bounds) for bounds in ranges]):
            records.append(result.result())
            print(f"Downloaded range {records[-1]['start']}-{records[-1]['end']}; {len(records)}/{len(ranges)} complete", flush=True)
    records.sort(key=lambda item: item["start"])
    with partial.open("ab") as stream:
        for record in records:
            with (folder / f"{record['start']}-{record['end']}.bin").open("rb") as chunk:
                shutil.copyfileobj(chunk, stream, 8 * 1024 * 1024)
    assert partial.stat().st_size == size
    (OUT / "download-ranges.json").write_text(json.dumps({"preserved_prefix_bytes": prefix,
        "workers": 4, "range_url": url, "ranges": records,
        "note": "Final assembled official MD5 is checked separately before accepting the file."}, indent=2) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    curl(f"https://zenodo.org/api/records/{RECORD}", OUT / "zenodo-record.json")
    curl(f"https://zenodo.org/api/records/{RECORD}/versions/latest", OUT / "zenodo-latest.json")
    record = json.loads((OUT / "zenodo-record.json").read_text())
    latest = json.loads((OUT / "zenodo-latest.json").read_text())
    assert str(latest["id"]) == RECORD, "Upstream changed; review the dataset version explicitly."
    file = next(f for f in record["files"] if f["key"] == "TDCII2.8.h5")
    target = RAW / file["key"]
    reused = target.is_file()
    if not target.is_file() or target.stat().st_size != file["size"]:
        assert shutil.disk_usage(RAW).free > 2 * file["size"]
        partial = target.with_suffix(target.suffix + ".part")
        ranged_download(f"https://zenodo.org/records/{RECORD}/files/{file['key']}?download=1", partial, file["size"])
        assert partial.stat().st_size == file["size"]
        digest = hashes(partial)
        assert "md5:" + digest["md5"] == file["checksum"], "Official checksum mismatch; partial file retained."
        partial.rename(target)
    digest = hashes(target)
    assert digest["bytes"] == file["size"] and "md5:" + digest["md5"] == file["checksum"]
    data = {"path": str(target.relative_to(ROOT)), "official_filename": file["key"],
            "record_id": RECORD, "download_url": file["links"]["self"],
            "official_bytes": file["size"], "official_checksum": file["checksum"],
            "official_checksum_passed": True, "existing_file_reused": reused, **digest}
    orbit_name = "OrbitData/MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5"
    orbit = RAW / "MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5"
    orbit.parent.mkdir(parents=True, exist_ok=True)
    orbit_url = f"https://raw.githubusercontent.com/TriangleDataCenter/Triangle-Simulator/{SIM_PIN}/{orbit_name}"
    curl(orbit_url, orbit)
    original = subprocess.check_output(["git", "-C", str(ROOT / "external/triangle-simulator"), "show", f"{SIM_PIN}:{orbit_name}"])
    assert orbit.read_bytes() == original
    orbit_report = {"path": str(orbit.relative_to(ROOT)), "official_filename": orbit.name,
                    "download_url": orbit_url, "source_commit": SIM_PIN,
                    "source_git_blob": subprocess.check_output(["git", "-C", str(ROOT / "external/triangle-simulator"), "rev-parse", f"{SIM_PIN}:{orbit_name}"]).decode().strip(),
                    "matches_pinned_official_git_blob": True,
                    "official_md5": None, "official_md5_note": "GitHub does not publish a separate official MD5; verify pinned Git blob and local hashes.", **hashes(orbit)}
    result = {"schema_version": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "TDC II 2.8 realistic-orbit training set and matching published simulator orbit only.",
              "official_link_index": "https://github.com/TriangleDataCenter/Taiji-Data-Challenge-II-Docs-Links",
              "data": data, "orbit": orbit_report, "wall_seconds": time.perf_counter() - start,
              "all_download_checks_pass": True}
    (OUT / "download.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()

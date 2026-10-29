#!/usr/bin/env python3
"""
run_comparison.py - Run 3 matches each for v1.2f, v1.3, and v1.5 with clean names.
"""
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(HERE, ".venv", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable

MATCHES = [
    ("V12f_m1", "src/student/agent_v12f.py:Agent1", "v1.2f"),
    ("V12f_m2", "src/student/agent_v12f.py:Agent1", "v1.2f"),
    ("V12f_m3", "src/student/agent_v12f.py:Agent1", "v1.2f"),
    ("V13_m1", "src/student/agent_v13.py:Agent1", "v1.3"),
    ("V13_m2", "src/student/agent_v13.py:Agent1", "v1.3"),
    ("V13_m3", "src/student/agent_v13.py:Agent1", "v1.3"),
    ("V15_m1", "src/student/agent_v15.py:Agent1", "v1.5"),
    ("V15_m2", "src/student/agent_v15.py:Agent1", "v1.5"),
    ("V15_m3", "src/student/agent_v15.py:Agent1", "v1.5"),
]

def run_match(idx, item):
    name, left_spec, tag = item
    port = 6000 + (idx % 2) * 100
    cmd = [PY, "a3.py", "match", name, "FULL", "--left", left_spec,
           "--right", "full", "-p", str(port)]
    print(f"[{idx+1}/9] Starting {name} ({tag}) on port {port}...", flush=True)
    proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    m = re.search(r"replay\s*:\s*(\S+\.rcg)", out)
    r = re.search(r"result\s*:\s*(\S+) (\d+)-(\d+) (\S+)", out)
    if not (m and r):
        print(f"[{idx+1}/9] {name} FAILED: {out[-300:]}", flush=True)
        return name, tag, None, None
    a_name, ga, gb, b_name = r.groups()
    us, them = (int(ga), int(gb)) if a_name == name else (int(gb), int(ga))
    rcg_name = m.group(1)
    rcg_path = os.path.join(HERE, "logs", rcg_name)
    subprocess.run([PY, "scripts/match_report.py", rcg_path, "--team", name,
                    "--tag", tag], cwd=HERE, capture_output=True)
    print(f"[{idx+1}/9] {name} ({tag}): {us}-{them}  -> {rcg_name}", flush=True)
    return name, tag, (us, them), rcg_name

def main():
    print(f"=== Running 9 Matches Comparison (3 each for v1.2f, v1.3, v1.5) ===", flush=True)
    # Run in pairs with staggering to avoid port clash
    results = []
    # We run in pairs of 2
    for i in range(0, len(MATCHES), 2):
        batch = MATCHES[i:i+2]
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = [ex.submit(run_match, i + j, batch[j]) for j in range(len(batch))]
            for f in futs:
                results.append(f.result())
        time.sleep(2)

    # Sync replays into gibbs so viewer sees them immediately
    print("\nSyncing replays for a3.py watch...", flush=True)
    subprocess.run([PY, "a3.py", "watch", "--no-serve"], cwd=HERE)

    print("\n=== SUMMARY OF COMPARISON RUNS ===")
    by_tag = {}
    for name, tag, score, rcg in results:
        by_tag.setdefault(tag, []).append((name, score, rcg))

    for tag in ("v1.2f", "v1.3", "v1.5"):
        runs = by_tag.get(tag, [])
        scored = [r for r in runs if r[1] is not None]
        w = sum(1 for _, (u, t), _ in scored if u > t)
        d = sum(1 for _, (u, t), _ in scored if u == t)
        l = sum(1 for _, (u, t), _ in scored if u < t)
        gf = sum(u for _, (u, t), _ in scored)
        ga = sum(t for _, (u, t), _ in scored)
        print(f"\n{tag} (3 matches): W{w} D{d} L{l}  |  Goals {gf}-{ga}  |  GD: {gf - ga:+d}")
        for n, sc, rcg in runs:
            s_str = f"{sc[0]}-{sc[1]}" if sc else "FAILED"
            print(f"   {n:<8}: {s_str}   replay: {rcg}")

if __name__ == "__main__":
    main()

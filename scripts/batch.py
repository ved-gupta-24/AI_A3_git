#!/usr/bin/env python3
"""
batch.py - play N matches in parallel and summarise them.

    python3 scripts/batch.py --tag v1.2c -n 8 -j 4
    python3 scripts/batch.py --tag v12c_vs_v11 --right src/student/agent_v1.py:Agent1

Each match gets its own port and team name (<NAME><i>), is fed to
scripts/match_report.py --tag TAG (one row per match in runlogs/history.csv),
and a W/D/L + goals line is printed at the end.
"""
import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def play(i, a):
    name = f"{a.name}{i}"
    opp = "FULL" if a.right == "full" else f"OPP{i}"
    cmd = [PY, "a3.py", "match", name, opp, "--right", a.right,
           "-p", str(a.port + 100 * i)]
    if a.left:
        cmd += ["--left", a.left]
    if a.half:
        cmd += ["-t", str(a.half)]
    proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    m = re.search(r"replay\s*:\s*(\S+\.rcg)", out)
    r = re.search(r"result\s*:\s*(\S+) (\d+)-(\d+) (\S+)", out)
    if not (m and r):
        return name, None, out[-400:]
    a_name, ga, gb, b_name = r.groups()
    us, them = (int(ga), int(gb)) if a_name == name else (int(gb), int(ga))
    rcg = os.path.join(HERE, "logs", m.group(1))
    subprocess.run([PY, "scripts/match_report.py", rcg, "--team", name,
                    "--tag", a.tag], cwd=HERE, capture_output=True)
    return name, (us, them), rcg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--name", default="ME")
    ap.add_argument("-n", type=int, default=6)
    ap.add_argument("-j", type=int, default=3)
    ap.add_argument("--left", help="spec for our side (default agent.py)")
    ap.add_argument("--right", default="full")
    ap.add_argument("-t", "--half", type=int)
    ap.add_argument("--port", type=int, default=6000)
    a = ap.parse_args()
    with ThreadPoolExecutor(a.j) as ex:
        res = list(ex.map(lambda i: play(i, a), range(a.n)))
    w = d = l = gf = ga = 0
    for name, score, info in res:
        if score is None:
            print(f"  {name}: FAILED\n{info}")
            continue
        us, them = score
        gf, ga = gf + us, ga + them
        w, d, l = w + (us > them), d + (us == them), l + (us < them)
        print(f"  {name}: {us}-{them}   {os.path.basename(info)}")
    print(f"== {a.tag}: W{w} D{d} L{l}   goals {gf}-{ga}   "
          f"({len(res)} matches)")


if __name__ == "__main__":
    main()

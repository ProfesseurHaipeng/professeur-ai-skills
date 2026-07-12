#!/usr/bin/env python3
"""Generate a reproducible six-line coin cast; never presents it as prophecy."""
from __future__ import annotations

import argparse
import hashlib
import json
import random


def cast(seed: str, method: str = "three-coins") -> dict:
    if method not in {"three-coins", "yarrow-analogue"}:
        raise ValueError("method must be three-coins or yarrow-analogue")
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big"))
    lines = []
    for line_number in range(1, 7):
        if method == "three-coins":
            values = [rng.choice((2, 3)) for _ in range(3)]
            total = sum(values)
            line_type = {6: "old-yin", 7: "young-yang", 8: "young-yin", 9: "old-yang"}[total]
        else:
            total = rng.choice((6, 7, 8, 9))
            line_type = {6: "old-yin", 7: "young-yang", 8: "young-yin", 9: "old-yang"}[total]
        lines.append({"position": line_number, "value": total, "type": line_type, "changing": total in (6, 9)})
    return {"seed": seed, "method": method, "lines_bottom_to_top": lines, "warning": "Symbolic reflection only; not a forecast."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, help="A user-visible seed, not a secret")
    parser.add_argument("--method", default="three-coins")
    args = parser.parse_args()
    print(json.dumps(cast(args.seed, args.method), ensure_ascii=False, indent=2))

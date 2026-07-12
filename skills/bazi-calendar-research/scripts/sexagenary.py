#!/usr/bin/env python3
"""Compute transparent stem/branch labels; not a full BaZi or fortune engine."""
from __future__ import annotations

import argparse
import json

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
FIRST_MONTH_STEM = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}


def year_label(year: int) -> dict:
    offset = year - 4
    return {"stem": STEMS[offset % 10], "branch": BRANCHES[offset % 12], "label": STEMS[offset % 10] + BRANCHES[offset % 12]}


def month_label(year: int, solar_month_index: int) -> dict:
    if solar_month_index not in range(1, 13):
        raise ValueError("solar_month_index must be 1..12, where 1 is 寅 month")
    year_stem_index = (year - 4) % 10
    stem_index = (FIRST_MONTH_STEM[year_stem_index] + solar_month_index - 1) % 10
    branch_index = (2 + solar_month_index - 1) % 12
    return {"stem": STEMS[stem_index], "branch": BRANCHES[branch_index], "label": STEMS[stem_index] + BRANCHES[branch_index]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--solar-month-index", type=int, help="1=寅, 2=卯 ... 12=丑")
    args = parser.parse_args()
    result = {"year": args.year, "year_label": year_label(args.year), "convention": "year uses Gregorian year; month requires a verified solar-term boundary"}
    if args.solar_month_index is not None:
        result["month_label"] = month_label(args.year, args.solar_month_index)
    print(json.dumps(result, ensure_ascii=False, indent=2))

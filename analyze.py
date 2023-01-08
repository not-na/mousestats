#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  analyze.py
#
#  Copyright 2022 notna <notna@apparat.org>
#
#  This file is part of mousestats.
#
#  mousestats is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  mousestats is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mousestats.  If not, see <http://www.gnu.org/licenses/>.
#

from typing import List, Dict, Any, Tuple
import optparse
import os
import datetime
import glob
import json


BUTTON_ORDER = ["BTN_LEFT", "BTN_RIGHT", "BTN_MIDDLE", "REL_LEFT", "REL_RIGHT", "_hour"]

BUTTON_NAMES = {
    "BTN_LEFT": "Left",
    "BTN_RIGHT": "Right",
    "BTN_MIDDLE": "Middle",
    "REL_WHEEL": "Wheel",
    "REL_LEFT": "Extra-Left",
    "REL_RIGHT": "Extra-Right",
    "_hour": "Active hours",
}

LIFETIME = 20000000


def read_file(fname: str) -> Dict[int, Dict[str, Any]]:
    lines = []
    with open(fname, "r") as f:
        for line in f:
            lines.append(json.loads(line))

    out = {}
    for line in lines:
        t = datetime.datetime.strptime(line["time"], "%d.%m.%Y %H:%M:%S")
        line["_t"] = t
        line["_hour"] = 1  # For monthly hour count
        out[t.day * 24 - 24 + t.hour] = line

    return out


def find_files(datapath: str) -> List[str]:
    return sorted(glob.glob(os.path.join(os.path.expanduser(datapath), "data_*.jsonl")))


def find_months(datapath: str) -> List[Tuple[int, int]]:
    files = find_files(datapath)
    out = []

    for fname in files:
        year = int(fname[-13:-9], base=10)
        month = int(fname[-8:-6], base=10)
        out.append((year, month))

    return out


def get_month(datapath, year, month):
    fname = os.path.join(
        os.path.expanduser(datapath), f"data_{year:04}_{month:02}.jsonl"
    )
    if os.path.exists(fname):
        return read_file(fname)
    else:
        return {}


def sum_lines(lines) -> Dict[str, int]:
    out = {}
    for line in lines:
        for k, v in line.items():
            if k not in ["time", "_t"]:
                if k not in out:
                    out[k] = 0
                out[k] += v

    return out


def format_line(line, num_digits=7) -> str:
    l2 = {}
    for key in BUTTON_ORDER:
        l2[key] = line.get(key, 0)
    for k, v in line.items():
        l2[k] = v

    out = []

    for k, v in l2.items():
        name = BUTTON_NAMES[k] if k in BUTTON_NAMES else "Other"
        out.append(f"{name}: {v:{num_digits}}")

    return "\t".join(out)


def flatten_data(monthdata):
    out = []
    for m, v in monthdata.items():
        out.extend(v.values())

    return out


def print_summary(datapath):
    months_list = find_months(datapath)

    monthdata = {m: get_month(datapath, *m) for m in months_list}
    months = {m: sum_lines(v.values()) for m, v in monthdata.items()}

    flat_lines = flatten_data(monthdata)

    years = {}
    for m, v in months.items():
        if m[0] not in years:
            years[m[0]] = {}
        years[m[0]] = sum_lines([years[m[0]], v])

    total = sum_lines(months.values())

    print("\nMonthly sums:")
    for m, v in months.items():
        y, m = m
        print(f"{y}-{m:02}: {format_line(v)}")

    print("\nYearly sums:")
    for y, v in years.items():
        print(f"{y}:    {format_line(v)}")

    print("\nTotal:")
    print(f"         {format_line(total)}")

    print("\nSome rough estimates:")

    total_left_clicks = total.get("BTN_LEFT", 0)
    total_hours = sum(len(read_file(fname)) for fname in find_files(datapath))
    cph = total_left_clicks / total_hours
    print(
        f"{total_left_clicks} Left Clicks over roughly {total_hours}h => {cph:.2f} clicks/hour"
    )
    tot_hours = LIFETIME / cph
    print(
        f"Assuming a life expectancy of {LIFETIME} clicks, the left button should last"
        f" about {tot_hours:.2f}h (~{tot_hours/24/365:.2f}y) of normal usage"
    )

    # Second estimate including AFK time, based on delta between first record and now
    first_h = min(flat_lines, key=(lambda line: line["_t"]))["_t"]
    life_hours = (datetime.datetime.now() - first_h) / datetime.timedelta(hours=1)
    life_cph = total_left_clicks / life_hours
    life_expectancy = LIFETIME / life_cph
    print(
        f"First record is at {first_h}, total lifetime is about {life_hours:.2f}h (~{life_hours/24/365:.2f}y, ~{total_hours/life_hours*100:.2f}% active)"
    )
    print(
        f"Using the total lifetime, expected total lifetime is about {life_expectancy:.2f}h (~{life_expectancy/24/365:.2f}y, {life_cph:.2f} CPH)"
    )

    # TODO: add more advanced stats, e.g. yearly trends


def main():
    oparser = optparse.OptionParser()
    oparser.add_option(
        "--datapath",
        dest="datapath",
        help="Base data directory for storing statistics",
        default="~/.local/share/mousestats/",
    )

    options, args = oparser.parse_args()

    datapath = options.datapath

    nfiles = len(find_files(datapath))
    print(f"Datapath is {datapath}, containing {nfiles} data files")
    if nfiles == 0:
        print("ERROR: Found no data files! No statistics will be calculated.")
        print("Use the --datapath argument to specify the base data directory")
        return

    print("Summary per month, year and total:")
    print_summary(datapath)


if __name__ == "__main__":
    main()

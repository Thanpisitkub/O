#!/usr/bin/env python3
"""Extracts the names of the Apoli / Origins power, action and condition types from the Forge-port
sources and writes tools/apoli_types.json (used by validate_project.py to catch typos in "type": "...").

Usage: gen_apoli_types.py <apoli_repo_root> <origins_repo_root> [out.json]

    apoli_repo_root   a clone of EdwinMindcraft/apoli   (1.20.1 branch, version 2.9.x)
    origins_repo_root a clone of EdwinMindcraft/origins-architectury (1.20.1 branch, version 1.10.x)

The result is a deliberate SUPERSET (every string that is the first argument of a registration call);
it is meant for typo detection only - the category (power / entity action / bientity condition ...) of a
type is not checked.
"""
import json
import os
import re
import sys

apoli, origins = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "apoli_types.json")


def scan(paths):
    names = set()
    for base in paths:
        files = [base] if os.path.isfile(base) else [
            os.path.join(d, f) for d, _, fs in os.walk(base) for f in fs if f.endswith(".java")]
        for f in files:
            text = open(f, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'\b\w+\(\s*"([a-z][a-z0-9_]*)"', text):
                names.add(m.group(1))
    return sorted(names)


ap = scan([os.path.join(apoli, "src/main/java/io/github/edwinmindcraft/apoli/common/registry"),
           os.path.join(apoli, "src/main/java/io/github/edwinmindcraft/apoli/api/MetaFactories.java")])
og = scan([os.path.join(origins, "src/main/java/io/github/apace100/origins/registry"),
           os.path.join(origins, "src/main/java/io/github/apace100/origins/power"),
           os.path.join(origins, "src/main/java/io/github/apace100/origins/condition")])
json.dump({"_comment": "Superset extracted from the Apoli 2.9.x / Origins 1.10.x Forge sources by gen_apoli_types.py; typo detection only.",
           "apoli": ap, "origins": og}, open(out, "w", encoding="utf-8"), indent=1)
print(f"wrote {out}: {len(ap)} apoli names, {len(og)} origins names")

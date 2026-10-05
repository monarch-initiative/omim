#!/usr/bin/env python3
"""
Structural checks on the produced LinkML YAML (see mondo-source-ingest Phase 9).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def main() -> None:
    p = argparse.ArgumentParser(
        description="Structural checks on produced LinkML YAML (labels, parents, ids, version)"
    )
    p.add_argument("--yaml", type=Path, required=True)
    p.add_argument(
        "--expected-version",
        default=None,
        help="If set, YAML version must equal this upstream release id",
    )
    p.add_argument(
        "--raw-json",
        type=Path,
        default=None,
        help="Optional acquire output: entity count cross-check",
    )
    args = p.parse_args()

    if not args.yaml.exists():
        print(f"ERROR: YAML not found: {args.yaml}", file=sys.stderr)
        sys.exit(1)

    with open(args.yaml, encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    version = doc.get("version")
    terms = doc.get("terms") or []
    title = doc.get("title")

    errors: list[str] = []

    if title is None or not str(title).strip():
        errors.append("OntologyDocument.title is missing or empty")
    if version is None or not str(version).strip():
        errors.append("OntologyDocument.version is missing or empty")

    expected_ver = args.expected_version
    if expected_ver is None and args.raw_json is not None and args.raw_json.exists():
        with open(args.raw_json, encoding="utf-8") as f:
            raw = json.load(f)
        rid = raw.get("release_id")
        if rid:
            expected_ver = rid

    if expected_ver is not None and version != expected_ver:
        errors.append(
            f"version mismatch: YAML has {version!r}, expected upstream {expected_ver!r}"
        )

    ids: set[str] = set()
    dup: list[str] = []
    missing_ids = 0
    for t in terms:
        tid = t.get("id")
        if tid is None or not str(tid).strip():
            missing_ids += 1
            continue
        tid = str(tid).strip()
        if tid in ids:
            dup.append(tid)
        ids.add(tid)
    if missing_ids:
        errors.append(f"terms with missing/empty id: {missing_ids}")
    if dup:
        errors.append(f"duplicate term ids (first 10): {dup[:10]}")

    empty_labels = 0
    for t in terms:
        lab = t.get("label")
        if lab is None or not str(lab).strip():
            empty_labels += 1
    if empty_labels:
        errors.append(f"terms with missing/empty label: {empty_labels}")

    broken_parents: list[tuple[str, str]] = []
    for t in terms:
        tid = t.get("id")
        for par in t.get("parents") or []:
            if par not in ids:
                broken_parents.append((str(tid), str(par)))
    if broken_parents:
        sample = broken_parents[:15]
        errors.append(
            "parent id not found in terms (sample up to 15): "
            + "; ".join(f"{c}->{p}" for c, p in sample)
        )
        if len(broken_parents) > 15:
            errors.append(f"... and {len(broken_parents) - 15} more broken parent refs")

    if args.raw_json is not None:
        if not args.raw_json.exists():
            errors.append(f"raw JSON not found: {args.raw_json}")
        else:
            with open(args.raw_json, encoding="utf-8") as f:
                raw = json.load(f)
            n_ent = len(raw.get("entities") or {})
            n_terms = len(terms)
            if n_ent != n_terms:
                errors.append(
                    f"term count mismatch: YAML has {n_terms} terms, "
                    f"raw JSON has {n_ent} entities"
                )

    print(f"title: {title!r}")
    print(f"version: {version!r}")
    print(f"terms: {len(terms)}")
    print(f"unique ids: {len(ids)}")
    print(f"broken parent refs: {len(broken_parents)}")

    if errors:
        print("\nFAIL", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("\nVERIFY: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()

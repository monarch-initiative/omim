#!/usr/bin/env python3
"""
OMIM API JSON (from acquire.py) → LinkML YAML.

Mappings:
  mimNumber + OMIM prefix           → id (OMIM:<n>)
  preferredTitle                    → label
  textSectionList description/…     → definition
  includedTitles                    → exact_synonyms (objects)
  phenotypicSeriesNumber            → parents (OMIM:<series>) when present in dataset
  status moved|removed              → deprecated (replacement IRIs: future work)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from omim.datamodel import OntologyDocument, OntologyTerm, Synonym


def _strip(s: object | None) -> str | None:
    if s is None:
        return None
    t = str(s).replace("\u00a0", " ").strip()
    return t if t else None


class _QuotingDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.nodes.ScalarNode:
    if any(c in data for c in ",:{}[]"):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_QuotingDumper.add_representer(str, _represent_str)


def _definition_from_text_sections(entry: dict) -> str | None:
    parts: list[str] = []
    for wrapper in entry.get("textSectionList") or []:
        if not isinstance(wrapper, dict):
            continue
        ts = wrapper.get("textSection")
        if not isinstance(ts, dict):
            ts = wrapper
        name = str(ts.get("textSectionName") or "")
        if name in ("description", "clinicalFeatures", "text"):
            c = _strip(ts.get("textSectionContent"))
            if c:
                parts.append(c)
    if not parts:
        return None
    return "\n\n".join(parts)


def _preferred_title(entry: dict) -> str | None:
    t = _strip(entry.get("preferredTitle"))
    if t:
        return t
    titles = entry.get("titles")
    if isinstance(titles, dict):
        return _strip(titles.get("preferredTitle"))
    return None


def _exact_synonyms_from_titles(label: str, entry: dict) -> list[Synonym]:
    out: list[Synonym] = []
    seen: set[str] = set()

    def add_chunks(raw: object | None) -> None:
        s = _strip(raw)
        if not s:
            return
        for chunk in re.split(r"\s*;;\s*", s):
            for line in chunk.split("\n"):
                line = line.strip()
                if not line or line == label:
                    continue
                if line not in seen:
                    seen.add(line)
                    out.append(Synonym(synonym_text=line))

    add_chunks(entry.get("includedTitles"))
    titles = entry.get("titles")
    if isinstance(titles, dict):
        add_chunks(titles.get("alternativeTitles"))
    return out


def _included_titles_synonyms(preferred: str, raw: object | None) -> list[Synonym]:
    s = _strip(raw)
    if not s:
        return []
    out: list[Synonym] = []
    for chunk in re.split(r"\s*;;\s*", s):
        chunk = chunk.strip()
        if not chunk:
            continue
        # "title;symbol" — take full chunk as synonym if distinct from label
        if preferred and chunk == preferred:
            continue
        out.append(Synonym(synonym_text=chunk))
    return out


def _series_parents(entry: dict, valid_mim: set[str]) -> list[str]:
    raw = entry.get("phenotypicSeriesNumber")
    if raw is None:
        return []
    s = _strip(raw)
    if not s:
        return []
    parents: list[str] = []
    for part in re.split(r"\s*,\s*", s):
        part = part.strip()
        if not part:
            continue
        if part in valid_mim:
            parents.append(f"OMIM:{part}")
    return parents


def _entry_to_term(entry: dict, valid_mim: set[str]) -> OntologyTerm | None:
    raw_id = entry.get("mimNumber")
    if raw_id is None:
        return None
    mid = str(raw_id).strip()
    if not mid:
        return None

    label = _preferred_title(entry)
    if not label:
        return None

    status = _strip(entry.get("status")) or "live"
    deprecated = status in ("moved", "removed")

    definition = _definition_from_text_sections(entry)

    exact = _exact_synonyms_from_titles(label, entry)

    parents = _series_parents(entry, valid_mim)

    return OntologyTerm(
        id=f"OMIM:{mid}",
        label=label,
        definition=definition,
        exact_synonyms=exact or None,
        parents=parents or None,
        deprecated=deprecated if deprecated else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="OMIM JSON → LinkML YAML")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        raw = json.load(f)

    release_id = _strip(raw.get("release_id")) or "unknown"
    entities: dict[str, dict] = raw.get("entities") or {}
    valid_mim = set(entities.keys())

    terms: list[OntologyTerm] = []
    for _k, ent in sorted(entities.items(), key=lambda x: x[0]):
        t = _entry_to_term(ent, valid_mim)
        if t is not None:
            terms.append(t)

    doc = OntologyDocument(
        title="Online Mendelian Inheritance in Man (OMIM)",
        version=release_id,
        terms=terms,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = doc.model_dump(exclude_none=True, by_alias=True)
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump(
            payload,
            f,
            Dumper=_QuotingDumper,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    print(f"Written {args.output} ({len(terms)} terms)", file=sys.stderr)


if __name__ == "__main__":
    main()

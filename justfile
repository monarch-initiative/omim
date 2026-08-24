# OMIM API → LinkML (parallel path; official https://api.omim.org/api)
#
#   Does NOT replace makefile `all` / omim2obo. Legacy omim.owl unchanged.
#
#   just acquire      — full catalog (needs OMIM_API_KEY; long run)
#   just acquire-test — bounded acquire for local dev (--max-mims 1000)
#   just extract    — tmp/omim_raw.json → omim.linkml.yml
#   just validate   — linkml-validate
#   just verify     — scripts/verify.py
#   just check      — validate + verify
#   just data2owl   — omim.linkml.yml → omim.linkml.owl
#   just reports    — ROBOT measure + SPARQL QC on omim.linkml.owl (needs Docker: odkfull)
#   just build      — acquire → extract → validate → verify → data2owl
#   just build-test — same as build but acquire-test (bounded)
#   just linkml-all — build + reports
#   just iterate    — extract → validate → verify (skip acquire)
#   just build-release — doid/ordo-like extra bundle (distinct filenames)
#
# Auth: reuse legacy root .env (API_KEY). Optional env/.env overrides (OMIM_API_KEY aliases API_KEY).
# Or: make linkml / make linkml-test / make linkml-release

schema   := "linkml/mondo_source_schema.yaml"
raw_json := "tmp/omim_raw.json"
yaml_out := "omim.linkml.yml"
owl_out  := "omim.linkml.owl"

acquire:
    uv run python scripts/acquire.py --output {{raw_json}}

acquire-test:
    uv run python scripts/acquire.py --output {{raw_json}} --max-mims 1000

extract:
    uv run python scripts/extract.py --input {{raw_json}} --output {{yaml_out}}

validate:
    uv run python -m linkml.validator.cli -s {{schema}} -C OntologyDocument {{yaml_out}}

verify:
    uv run python scripts/verify.py --yaml {{yaml_out}} --raw-json {{raw_json}}

check: validate verify

data2owl:
    uv run python -m linkml_owl.dumpers.owl_dumper \
        --schema {{schema}} -f yaml -o tmp/omim.functional.owl {{yaml_out}}
    docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 \
        bash -lc 'robot convert -i tmp/omim.functional.owl -o tmp/omim.rdfxml.owl'
    mv tmp/omim.rdfxml.owl {{owl_out}}

# ROBOT runs inside odkfull so a local `robot` install is not required.
reports:
    #!/usr/bin/env bash
    set -euo pipefail
    test -f "{{owl_out}}" || { echo "Missing {{owl_out}} — run just data2owl or just build first." >&2; exit 1; }
    mkdir -p reports
    docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 \
      bash -lc 'mkdir -p reports && robot measure \
        --prefix "OMIM: http://purl.obolibrary.org/obo/OMIM_" \
        --prefix "OMIMPS: http://purl.obolibrary.org/obo/OMIMPS_" \
        -i omim.linkml.owl --format json --metrics extended --output reports/metrics.json && \
      robot query -i omim.linkml.owl \
        --query sparql/count_classes_by_top_level.sparql reports/top-level-counts.tsv'

build-release: build reports
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p mappings metadata reports
    # mirror OWL = same as component for OMIM (no separate mirror step)
    cp -f {{owl_out}} mirror-omim.owl
    # semsql DB
    uv run python scripts/extract_prefixes.py --input tmp/omim.functional.owl --output tmp/prefixes.csv
    docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 \
        bash -lc 'cp -f omim.linkml.owl tmp/omim-semsql.owl && \
            RUST_BACKTRACE=full semsql make tmp/omim-semsql.db -P tmp/prefixes.csv && \
            mv tmp/omim-semsql.db omim.db'
    # signatures
    docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 \
        bash -lc 'robot query -i mirror-omim.owl --query sparql/classes.sparql reports/mirror_signature-omim.tsv && \
            (head -n 1 reports/mirror_signature-omim.tsv && tail -n +2 reports/mirror_signature-omim.tsv | sort) > reports/mirror_signature-omim.tsv-temp && \
            mv reports/mirror_signature-omim.tsv-temp reports/mirror_signature-omim.tsv && \
            robot query -i omim.linkml.owl --query sparql/classes.sparql reports/component_signature-omim.tsv && \
            (head -n 1 reports/component_signature-omim.tsv && tail -n +2 reports/component_signature-omim.tsv | sort) > reports/component_signature-omim.tsv-temp && \
            mv reports/component_signature-omim.tsv-temp reports/component_signature-omim.tsv'
    # SSSOM
    docker run --rm -v "$PWD:/work" -w /work obolibrary/odkfull:v1.6 \
        bash -lc 'robot convert -i omim.linkml.owl -f json -o tmp/component-omim.json && \
            sssom parse tmp/component-omim.json -I obographs-json --prefix-map-mode merged -m metadata/omim.metadata.sssom.yml -o mappings/omim.sssom.tsv 2> reports/sssom-parse-warnings.log && \
            echo "sssom parse: $$(wc -l < reports/sssom-parse-warnings.log) warning line(s) → reports/sssom-parse-warnings.log" && \
            sssom sort mappings/omim.sssom.tsv -o mappings/omim.sssom.tsv'
    # metrics
    cp -f reports/metrics.json metadata/omim-metrics.json
    @echo "External bundle complete."

build: acquire extract validate verify data2owl

# Named linkml-all so it is not confused with makefile `all` (legacy).
linkml-all:
    @just build
    @just reports

build-test: acquire-test extract validate verify data2owl

iterate: extract validate verify

release:
    @echo "Parallel LinkML artefacts (legacy release unchanged):"
    @echo "  {{yaml_out}} {{owl_out}} mirror-omim.owl omim.db mappings/omim.sssom.tsv"
    @echo "Or: make linkml-release"

clean-linkml:
    rm -f {{yaml_out}} {{owl_out}} mirror-omim.owl omim.db
    rm -rf tmp/
    rm -f reports/metrics.json reports/top-level-counts.tsv reports/mirror_signature-omim.tsv reports/component_signature-omim.tsv reports/sssom-parse-warnings.log
    rm -f mappings/omim.sssom.tsv metadata/omim-metrics.json

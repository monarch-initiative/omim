.PHONY: all help install test scrape get-pmids cleanup \
	linkml-install acquire acquire-test extract validate verify data2owl \
	linkml linkml-test linkml-iterate linkml-reports linkml-release linkml-clean


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
# Legacy release path (unchanged). Parallel LinkML path: make linkml* — see README.
all: omim.ttl omim.sssom.tsv omim.owl mondo-omim-genes.robot.tsv disease-gene-relationships-qc.tsv

# build: Create new omim.ttl
# - OMIM datasets in data/ dependencies are downloaded by the script at runtime
omim.ttl:
	 make mondo_exactmatch_omim.sssom.tsv -B
	 make data/hgnc/hgnc_complete_set.txt -B
	 python3 -m omim2obo
	 make cleanup

data/hgnc/hgnc_complete_set.txt:
	@echo "Downloading HGNC complete set..."
	@mkdir -p data/hgnc
	wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 --tries=3 \
		--continue --progress=bar:force \
		"https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt" -O $@.tmp
	@echo "Verifying download..."
	@if [ ! -s $@.tmp ]; then \
		echo "ERROR: Downloaded file is empty!"; \
		rm -f $@.tmp; \
		exit 1; \
	fi
	@line_count=$$(wc -l < $@.tmp | tr -d ' '); \
	if [ $$line_count -lt 40000 ]; then \
		echo "ERROR: Downloaded file has only $$line_count lines (expected >40000)"; \
		rm -f $@.tmp; \
		exit 1; \
	fi
	@if ! head -1 $@.tmp | grep -q "hgnc_id"; then \
		echo "ERROR: Downloaded file doesn't have expected header"; \
		rm -f $@.tmp; \
		exit 1; \
	fi
	@mv $@.tmp $@
	@echo "✓ Successfully downloaded and verified HGNC file ($$line_count lines)"

omim.sssom.tsv: omim.json
	sssom parse omim.json -I obographs-json -m data/metadata.sssom.yml -o omim.sssom.tsv
	make cleanup

mondo_exactmatch_omim.sssom.tsv:
	wget "http://purl.obolibrary.org/obo/mondo/mappings/mondo_exactmatch_omim.sssom.tsv" -O $@

mondo_exactmatch_omimps.sssom.tsv:
	wget "http://purl.obolibrary.org/obo/mondo/mappings/mondo_exactmatch_omimps.sssom.tsv" -O $@

%.sssom.owl: %.sssom.tsv
	sssom convert $< -O owl -o $@

# More commands / goals  -----------------------------------------------------------------------------------------------
# Create mapping artefact(s)
omim.json: omim.owl
	robot convert -i $< -o omim.json

# Create OWL artefact, but adding HGNC links alongside the OMIM genes and
# Mondo mappings alongside the OMIM diseases
omim.owl: omim.ttl mondo_exactmatch_omim.sssom.owl mondo_exactmatch_omimps.sssom.owl
	robot merge $(patsubst %, -i %, $^) \
		query --update sparql/add_flipped_mondo_mappings.ru \
		query --update sparql/hgnc_links.ru \
		convert -f ofn -o $@

# Create a TSV of relational information for gene and disease classes
mondo-omim-genes.tsv: omim.owl
	robot query -i $< --query sparql/mondo-omim-genes.sparql $@

# Create a TSV of relational information for gene and disease classes, as a ROBOT template
mondo-omim-genes.robot.tsv: mondo-omim-genes.tsv
	python -m omim2obo.mondo_omim_genes_robot_tsv --inpath $< --outpath $@

# Create a QC file of MIM-RO-MIM Gene-to-Disease associations in omim.ttl
disease-gene-relationships-qc.tsv: omim.ttl
	robot query -i $< --query sparql/disease-gene-relationships.sparql $@

cleanup:
	@rm -f omim.json

# scrape: argument should be in form of YYYY/MM or YYYY/mm
# @param y: The year. Pass as <FLAG>=<YYYY>, where <FLAG> can be y, yr, year, or YYYY.
# @param m: The month. Pass as <FLAG>=<MM>, where <FLAG> can be m, mon, month, mm, or MM.
# @examples
# -"make scrape y=2021 m=5
scrape:
	@{ \
    set -e ;\
	arg1=$(y)$(yr)$(year)$(YYYY) ;\
	arg2=$(m)$(mon)$(month)$(mm)$(MM) ;\
	 python -m omim2obo.omim_code_scraper $$arg1/$$arg2 ;\
    }

# Get list of OMIM codes and PMIDs in format of "OMIM PMID"
get-pmids:
	 python3 -m omim2obo.omim_code_pmid_query

# SETUP / INSTALLATION -------------------------------------------------------------------------------------------------
install:
	pip install -r requirements-unlocked.txt --user --break-system-packages

# QA / TESTING ---------------------------------------------------------------------------------------------------------
test:
	 python3 -m unittest discover -v

# PARALLEL LINKML PATH (additive; does not replace `all`) -------------------------------------------------------------
# Run via ./run.sh make … (same ODK wrapper as legacy `all`). Recipes call robot/semsql/sssom
# directly; do not spawn docker from make.
# Auth: legacy root .env API_KEY (same as omim2obo / MONARCH_OMIM_API_KEY in CI).
# Outputs use distinct names (omim.linkml.yml / omim.linkml.owl) so legacy omim.owl is never overwritten.
OMIM_SCHEMA := linkml/mondo_source_schema.yaml
OMIM_JSON := tmp/omim_raw.json
OMIM_YAML := omim.linkml.yml
OMIM_OWL := omim.linkml.owl

linkml-install:
	pip install -e .

acquire:
	python3 scripts/acquire.py --output $(OMIM_JSON)

acquire-test:
	python3 scripts/acquire.py --output $(OMIM_JSON) --max-mims 1000

extract:
	python3 scripts/extract.py --input $(OMIM_JSON) --output $(OMIM_YAML)

validate:
	python3 -m linkml.validator.cli -s $(OMIM_SCHEMA) -C OntologyDocument $(OMIM_YAML)

verify:
	python3 scripts/verify.py --yaml $(OMIM_YAML) --raw-json $(OMIM_JSON)

data2owl:
	mkdir -p tmp
	# Assumes linkml-owl is on ODK's python (same as ./run.sh).
	python3 -m linkml_owl.dumpers.owl_dumper \
		--schema $(OMIM_SCHEMA) -f yaml -o tmp/omim.functional.owl $(OMIM_YAML)
	robot convert -i tmp/omim.functional.owl -o $(OMIM_OWL)

linkml: acquire extract validate verify data2owl

linkml-test: acquire-test extract validate verify data2owl

linkml-iterate: extract validate verify

linkml-reports:
	@test -f "$(OMIM_OWL)" || { echo "Missing $(OMIM_OWL) — run make data2owl or make linkml first." >&2; exit 1; }
	mkdir -p reports
	robot measure \
		--prefix "OMIM: http://purl.obolibrary.org/obo/OMIM_" \
		--prefix "OMIMPS: http://purl.obolibrary.org/obo/OMIMPS_" \
		-i $(OMIM_OWL) --format json --metrics extended --output reports/metrics.json
	robot query -i $(OMIM_OWL) \
		--query sparql/count_classes_by_top_level.sparql reports/top-level-counts.tsv

linkml-release: linkml linkml-reports
	mkdir -p tmp mappings metadata reports
	cp -f $(OMIM_OWL) mirror-omim.owl
	python3 scripts/extract_prefixes.py --input tmp/omim.functional.owl --output tmp/prefixes.csv
	cp -f $(OMIM_OWL) tmp/omim-semsql.owl
	RUST_BACKTRACE=full semsql make tmp/omim-semsql.db -P tmp/prefixes.csv
	mv tmp/omim-semsql.db omim.db
	robot query -i mirror-omim.owl --query sparql/classes.sparql reports/mirror_signature-omim.tsv
	(head -n 1 reports/mirror_signature-omim.tsv && tail -n +2 reports/mirror_signature-omim.tsv | sort) > reports/mirror_signature-omim.tsv-temp
	mv reports/mirror_signature-omim.tsv-temp reports/mirror_signature-omim.tsv
	robot query -i $(OMIM_OWL) --query sparql/classes.sparql reports/component_signature-omim.tsv
	(head -n 1 reports/component_signature-omim.tsv && tail -n +2 reports/component_signature-omim.tsv | sort) > reports/component_signature-omim.tsv-temp
	mv reports/component_signature-omim.tsv-temp reports/component_signature-omim.tsv
	robot convert -i $(OMIM_OWL) -f json -o tmp/component-omim.json
	sssom parse tmp/component-omim.json -I obographs-json --prefix-map-mode merged -m metadata/omim.metadata.sssom.yml -o mappings/omim.sssom.tsv 2> reports/sssom-parse-warnings.log
	@echo "sssom parse: $$(wc -l < reports/sssom-parse-warnings.log) warning line(s) → reports/sssom-parse-warnings.log"
	sssom sort mappings/omim.sssom.tsv -o mappings/omim.sssom.tsv
	cp -f reports/metrics.json metadata/omim-metrics.json
	@echo "External bundle complete."

linkml-clean:
	rm -f $(OMIM_YAML) $(OMIM_OWL) mirror-omim.owl omim.db
	rm -rf tmp/
	rm -f reports/metrics.json reports/top-level-counts.tsv reports/mirror_signature-omim.tsv reports/component_signature-omim.tsv reports/sssom-parse-warnings.log
	rm -f mappings/omim.sssom.tsv metadata/omim-metrics.json

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "----------------------------------------"
	@echo "	Command reference: OMIM"
	@echo "----------------------------------------"
	@echo "all"
	@echo "Creates all legacy release artefacts.\n"
	@echo "omim.ttl"
	@echo "Creates main release artefact: omim.ttl\n"
	@echo "omim.sssom.tsv"
	@echo "Creates an SSSOM TSV of OMIM terms.\n"
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "test"
	@echo "Runs unit tests.\n"
	@echo "scrape"
	@echo "Does web scraping to get information about some OMIM terms.\n"
	@echo "get-pmids"
	@echo "Gets PMIDs for all terms.\n"
	@echo "linkml-install / linkml / linkml-test / linkml-release"
	@echo "Parallel API→LinkML path (see README). Does not change legacy all.\n"

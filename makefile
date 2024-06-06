.PHONY: all help install test scrape get-pmids cleanup


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: omim.ttl omim.sssom.tsv omim.owl mondo_genes.robot.tsv

# build: Create new omim.ttl
omim.ttl:
	 python3 -m omim2obo
	 make cleanup

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

mondo_genes.robot.tsv: omim.owl
	# Create a TSV of relational information for gene and disease classes
	robot query -i omim.owl --query sparql/mondo_genes.sparql $@
	# Insert the source_code column as the second to last column
	awk 'BEGIN {FS=OFS="\t"} {if (NR==1) {$$(NF+1)=$$(NF); $$(NF-1)="?source_code";} else {$$(NF+1)=$$(NF); $$(NF-1)="MONDO:OMIM";}} 1' $@ > temp_file && mv temp_file $@
	# Remove the first character of each field in the header
	awk 'BEGIN {FS=OFS="\t"} NR==1 {for (i=1; i<=NF; i++) $$i=substr($$i, 2)} {print}' $@ > temp_file && mv temp_file $@
	# Remove < and > characters from specified columns
	awk 'BEGIN {FS=OFS="\t"} NR>1 {gsub(/^<|>$$/, "", $$1); gsub(/^<|>$$/, "", $$2); gsub(/^<|>$$/, "", $$5)} {print}' $@ > temp_file && mv temp_file $@
	# Insert ROBOT subheader
	robot_subheader="ID\tSC 'has material basis in germline mutation in' some %\t>A oboInOwl:source\t>A oboInOwl:source\t" && \
	sed 1a"$$robot_subheader" $@ > temp_file && mv temp_file $@

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
	pip install -r requirements-unlocked.txt

# QA / TESTING ---------------------------------------------------------------------------------------------------------
test:
	 python3 -m unittest discover -v

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "----------------------------------------"
	@echo "	Command reference: OMIM"
	@echo "----------------------------------------"
	@echo "all"
	@echo "Creates all release artefacts.\n"
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

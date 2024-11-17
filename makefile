.PHONY: all help install test scrape get-pmids cleanup


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: omim.ttl omim.sssom.tsv omim.owl mondo-omim-genes.robot.tsv

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

# Create a TSV of relational information for gene and disease classes
mondo-omim-genes.tsv: omim.owl
	robot query -i omim.owl --query sparql/mondo-omim-genes.sparql $@

# Create a TSV of relational information for gene and disease classes, as a ROBOT template
mondo-omim-genes.robot.tsv: mondo-omim-genes.tsv
	python -m omim2obo.mondo_omim_genes_robot_tsv --inpath $< --outpath $@

# Ad hoc: Create a TSV of MIM-RO-MIM Gene-to-Disease realtions in omim.ttl
disease-gene-relationships.tsv: omim.ttl
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

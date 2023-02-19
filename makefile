.PHONY: all help install test scrape get-pmids automated-release


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: omim.ttl omim.sssom.tsv mondo_non_disease_exclusions.tsv
automated-release: omim.ttl mondo_non_disease_exclusions.tsv

# build: Create new omim.ttl
omim.ttl:
	 python3 -m omim2obo
	 @rm omim.json

omim.sssom.tsv: omim.json
	sssom parse omim.json -I obographs-json -m data/metadata.sssom.yml -o omim.sssom.tsv
	@rm omim.json

mondo_non_disease_exclusions.tsv:
	 python3 omim2obo/utils/mondo_non_disease_exclusions/mondo_non_disease_exclusions.py \
		--symbolic-prefixes-path data/symbolic_prefixes.tsv \
		--mim-titles-path data/mimTitles.txt \
		--outpath mondo_non_disease_exclusions.tsv

# More commands / goals  -----------------------------------------------------------------------------------------------
# Create mapping artefact(s)
omim.json:
	robot convert -i omim.ttl -o omim.json

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
	pip install -r requirements.txt

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
	@echo "automated-release"
	@echo "Creates all release artefacts that are currently easy to handle by a GitHub Action automated release. omim.sssom.tsv is excluded because of robot dependency. \n"
	@echo "omim.ttl"
	@echo "Creates main release artefact: omim.ttl\n"
	@echo "omim.sssom.tsv"
	@echo "Creates an SSSOM TSV of OMIM terms.\n"
	@echo "mondo_non_disease_exclusions.tsv"
	@echo "Generates a Mondo intesional exclusions TSV file with non-diseases as its contents.\n"
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "test"
	@echo "Runs unit tests.\n"
	@echo "scrape"
	@echo "Does web scraping to get information about some OMIM terms.\n"
	@echo "get-pmids"
	@echo "Gets PMIDs for all terms.\n"

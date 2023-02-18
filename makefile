.PHONY: all help install test build build-cleanup scrape get-pmids sssom sssom-clean


# MAIN COMMANDS --------------------------------------------------------------------------------------------------------
all: build sssom build-cleanup

# Create new omim.ttl
build:
	 python3 -m omim2obo

build-cleanup:
	@rm omim.json

# Additional ad hoc commands -------------------------------------------------------------------------------------------
# Create mapping artefact(s)
omim.json:
	robot convert -i omim.ttl -o omim.json

omim.sssom.tsv:
	sssom parse omim.json -I obographs-json -m data/metadata.sssom.yml -o omim.sssom.tsv

sssom-clean:
	@rm omim.json; rm omim.sssom.tsv

sssom: sssom-clean omim.json omim.sssom.tsv

# scrape: argument should be in form of YYYY/MM or YYYY/mm
# @param y: The year. Pass as <FLAG>=<YYYY>, where <FLAG> can be y, yr, year,
#           or YYYY.
# @param m: The month. Pass as <FLAG>=<MM>, where <FLAG> can be m, mon, month,
#           mm, or MM.
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
	@echo "install"
	@echo "Install's Python requirements.\n"
	@echo "all"
	@echo "Creates all release artefacts.\n"
	@echo "build"
	@echo "Creates main release artefact: omim.ttl\n"
	@echo "build-cleanup"
	@echo "Removes any remaining files after build completes.\n"
	@echo "sssom-clean"
	@echo "Removes any remaining artefacts after creating SSSOM TSV.\n"
	@echo "test"
	@echo "Runs unit tests.\n"
	@echo "scrape"
	@echo "Does web scraping to get information about some OMIM terms.\n"
	@echo "get-pmids"
	@echo "Gets PMIDs for all terms.\n"

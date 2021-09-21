SRC=omim2obo/

.PHONY: all lint tags ltags test lintall codestyle docstyle lintsrc \
linttest doctest doc docs code linters_all codesrc codetest docsrc \
doctest build dist pypi-push-test pypi-push pypi-test pip-test pypi \
pip remove-previous-build build-package get-pmids scrape


# MAIN COMMANDS ----------------------------------------------------------------
# TODO: What else needs to be done before build? How to chain together?
all: build

# Create new omim.ttl
build:
	pipenv run python3 -m omim2obo

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
	pipenv run python -m omim2obo.omim_code_scraper $$arg1/$$arg2 ;\
    }

# Get list of OMIM codes and PMIDs in format of "OMIM PMID"
get-pmids:
	pipenv run python3 -m omim2obo.omim_code_pmid_query

# CODE QUALITY -----------------------------------------------------------------
# Batched Commands
# - Code & Style Linters
lint: lintsrc codesrc docsrc
linters_all: doc code lintall

# Pylint Only
PYLINT_BASE =pipenv run python3 -m pylint --output-format=colorized --reports=n
lintall: lintsrc linttest
lintsrc:
	${PYLINT_BASE} ${SRC}
linttest:
	${PYLINT_BASE} test/

# PyCodeStyle Only
PYCODESTYLE_BASE=pipenv run python3 -m pycodestyle
codestyle: codestylesrc codestyletest
codesrc: codestylesrc
codetest: codestyletest
code: codestyle
codestylesrc:
	${PYCODESTYLE_BASE} ${SRC}
codestyletest:
	 ${PYCODESTYLE_BASE} test/

# PyDocStyle Only
PYDOCSTYLE_BASE=pipenv run python3 -m pydocstyle
docstyle: docstylesrc docstyletest
docsrc: docstylesrc
doctest: docstyletest
docs: docstyle
docstylesrc:
	${PYDOCSTYLE_BASE} ${SRC}
docstyletest:
	${PYDOCSTYLE_BASE} test/
codetest:
	pipenv run python -m pycodestyle test/
codeall: code codetest
doc: docstyle

# Testing
test:
	pipenv run python3 -m unittest discover -v
testdoc:
	pipenv run python3 -m test.test --doctests-only
testall: test testdoc
test-survey-cto: #TODO: run a single unit test
	pipenv run python3 -m unittest discover -v


# PACKAGE MANAGEMENT  ----------------------------------------------------------
remove-previous-build:
	rm -rf ./dist; 
	rm -rf ./build; 
	rm -rf ./*.egg-info
build-package: remove-previous-build
	python3 setup.py sdist bdist_wheel
dist: build-package
pypi-push-test: build-package
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
pypi-push:
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*; \
	make remove-previous-build
pypi-test: pypi-push-test
pip-test: pypi-push-test
pypi: pypi-push
pip: pypi-push

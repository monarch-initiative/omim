# OMIM Data Pipeline Tools

## Setup
### 1. Install Python
- [RealPython blog install guide](https://realpython.com/installing-python/): My preferred guide for installing on Windows or Mac
- [Python documentation for installing on Windows](https://docs.python.org/3/using/windows.html)
- [Python documentation for installing on Mac](https://docs.python.org/3/using/mac.html)

### 2. Setup virtual environment & installing packages
There are various ways to do this in Python. We use Pipenv: https://docs.python-guide.org/dev/virtualenvs/#installing-pipenv
1. Run: `pip install pipenv` (if you don't have it installed already)
2. Change directory: `cd <PATH/TO/CLONED_PROJECT_FOLDER>`
3. Run: `pipenv install`
4. There is a known possible issue with dependency `psutil` on some systems. If 
you get an error related to this when installing, ignore it, as it is does not 
seem to be needed to run any of the tools. If however you do get a `psutil` error
when running anything, please let us know by [creating an issue](https://github.com/monarch-initiative/omim/issues/new).

## Tools: Running the full pipeline
TODO: Not yet created. Currently, this is an alias for `make build`.

Command: `make all`


## Tool 1/3: OMIM 2 OBO
Running this program will create a new `data/omim.ttl` file.

Command: `make build`


## Tool 2/3: Get PMIDs used for OMIM codes from `omim.ttl`
### Requirements
There must be an `omim.ttl` file inside of `data/`.

Command: `make get-pmids`


## Tool 3/3: OMIM Code Web Scraper
Tool for ingesting data from [omim.org](https://omim.org).

Currently, the only feature is `get_codes_by_yyyy_mm`, which returns a list of 
OMIM codes and their prefixes from https://omim.org/statistics/update.

### Usage: Command Line Interface
#### Syntax
1. `make scrape y=<YEAR> m=<MONTH>`
2. `make scrape y=<YEAR> m=<MONTH> > <path/to/outputFile>`

#### Usage
1. Get codes for May 2021, printed to terminal: `make scrape y=2021 m=5`
2. Get codes for May 2021 and output to a file "myfile.txt": `make scrape y=2021 m=5 > myfile.txt`

#### Examples
Command:  
`make scrape y=2021 m=5`

Response:
```py
[('#', '619340'),
 ('#', '619355'),
 ('*', '619357'),
 ('*', '619358'),
 ('*', '619359'),
 ('#', '619325'),
 ('#', '619328'),
 ('*', '100850'),
 ...
 ('#', '613102')]
 ```

### Usage: Python API
Using `get_codes_by_yyyy_mm()` will return a list of tuples.

```py
from omim2obo.omim_code_scraper import get_codes_by_yyyy_mm

code_tuples = get_codes_by_yyyy_mm('2021/05')
```

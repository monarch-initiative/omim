# OMIM Data Pipeline Tools

## About OMIM & this repository
OMIM stands for "Online Mendelian Inheritance in Man", and is an online 
catalog of human genes and genetic disorders. The official site is: https://omim.org/

This purpose of this repository is for data transformations for ingest into Mondo. Mainly, 
it is for generating an `omim.ttl` and other release artefacts.

Disclaimer: This repository and its created data artefacts are unnofficial. For 
official, up-to-date OMIM data, please visit [omim.org](https://omim.org).

## Setup
### 1. API Key and `.env`
1. Run: `cp .env.example .env`
2. Change the value of `API_KEY` to your own. If you don't have one, you can request
one at https://omim.org/downloads. This will probably be sufficient for the purposes
of downloading the necessary text files, but if not, you can also require access to
the REST API as well: https://omim.org/api.
   
### 2. Python dependencies
#### 2.1 Python installation
- [RealPython blog install guide](https://realpython.com/installing-python/): My preferred guide for installing on Windows or Mac
- [Python documentation for installing on Windows](https://docs.python.org/3/using/windows.html)
- [Python documentation for installing on Mac](https://docs.python.org/3/using/mac.html)

#### 2.2 Setup virtual environment & installing packages
1. Run: `make install`
2. There is a known possible issue with dependency `psutil` on some systems. If 
you get an error related to this when installing, ignore it, as it is does not 
seem to be needed to run any of the tools. If however you do get a `psutil` error
when running anything, please let us know by [creating an issue](https://github.com/monarch-initiative/omim/issues/new).

## Running & creating release
Run: `sh run.sh make all`

Running this will create new release artefacts in the root directory.

You can also run `make build` or `python -m omim2obo`. These are all the same 
command. This will download files from omim.org and run the build.

Offline/cache option: `python -m omim2obo --use-cache`
If there's an issue downloading the files, or you are offline, or you just want 
to use the cache anyway, you can pass the `--use-cache` flag.

## Additional tools
<details><summary>Details</summary>
<p>

### Get PMIDs used for OMIM codes from `omim.ttl`
Command: `sh run.sh make get-pmids`

### OMIM Code Web Scraper
Currently, the only feature is `get_codes_by_yyyy_mm`, which returns a list of 
OMIM codes and their prefixes from https://omim.org/statistics/update.

#### Usage: Command Line Interface
##### Syntax
1. `make scrape y=<YEAR> m=<MONTH>`
2. `make scrape y=<YEAR> m=<MONTH> > <path/to/outputFile>`

##### Usage
1. Get codes for May 2021, printed to terminal: `make scrape y=2021 m=5`
2. Get codes for May 2021 and output to a file "myfile.txt": `make scrape y=2021 m=5 > myfile.txt`

##### Examples
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

</p>
</details> 

## Release files
- `omim.ttl`: OMIM ontologized
- `omim.sssom.tsv`: SSSOM mapping file
- `mondo-omim-genes.robot.tsv`: ROBOT template for adding OMIM genes to Mondo
- `review.tsv`: Special cases to consider for manual review

Notice: These are generated based on the latest downloadable data files from [omim.org](https://omim.org), updated 
daily, rather than what is seen on the _omim.org/entry/MIM#_ pages. Note that the data files and the entry pages aren't 
always in sync, and that one or the other may be slightly more up-to or out-of date for a period of time.

### `review.tsv`
Columns:
- `classCode`: integer: ID of review case class
- `classShortName`: string (camelCase): describing the review case class
- `value`: any: Some form of data to review
- `comment`: string (optional)

#### 1. `causalD2gButMarkedDigenic`
This review case involves what would be otherwise considered a valid disease-gene relationship, but for the fact that  
it quite unusually includes 'digenic' in the label, even though it only had 1 association. OMIM doesn't have a 
guarnatee on the data quality of its disease-gene associations marked 'digenic', so for any of these entries, it could 
be the case that either (a) it is not 'digenic'; OMIM should remove that from the label, and Mondo can make an explicit 
exception to add the relationship, or could otherwise wait until OMIM fixes the issue and it will automatically be 
added, or (b) it is in fact 'digenic', and OMIM should add the missing 2nd gene association.

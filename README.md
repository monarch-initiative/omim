# OMIM Ingest

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

## Curator configuration files
**[protected-disease-gene.tsv](https://github.com/monarch-initiative/omim/blob/main/data/protected-disease-gene.tsv)**
This file contains a list of disease-gene associations that should not be removed from the ontology, even if the 
pipeine logic would otherwise determine that the association is not disease-defining. As of 2025/03/06, the only `type`
of protection in the file is 'digenic'. For this protection type, there should be 2 rows for a given phenotype MIM. The 
following fields are required for each row: `phenotype_mim`, `type`, `gene_mim`, `hgnc_id`)  should be filled out 
in each row. `orcid` is optional but encouraged. `comment`, `mondo_id`, and `mondo_label` are all optional and not used 
in any programmatic way.

**[exclusions-disease-gene.tsv](https://github.com/monarch-initiative/omim/blob/main/data/exclusions-disease-gene.tsv)**
This file contains a list of disease-gene associations that should be removed from the ontology, even if the 
pipeine logic would otherwise determine that the association is disease-defining. There is more information about this 
in the section describing `review.tsv`. 

**[known_capitalizations.tsv](https://github.com/monarch-initiative/omim/blob/main/data/known_capitalizations.tsv).**
These are known replacements where we want to take matching text (lowercase or otherwise), and replace it with what is 
shown in the `cap_name` column. There is also a `lower_name` column, which represents the full lowercasing of the 
string. However, it is a bit superfluous, as it will ensure that any capitalization variation of the string in 
`cap_name` will get re-capitalized to what is in `cap_name`. E.g. if `cap_name` is "Prune Belly Syndrome", then "prune 
belly syndrome", or "Prune belly syndrome" would both be replaced with "Prune Belly Syndrome". This logic operates only 
on OMIM titles (standard title, as well as alt, formerly, and included titles).

## Additional tools
<details><summary>Details</summary>
<p>

### Get PMIDs used for OMIM codes from `omim.ttl`
Command: `sh run.sh make get-pmids`

### OMIM Code Web Scraper
Currently, the only feature is `get_codes_by_yyyy_mm`, which returns a list of OMIM codes and their prefixes from 
https://omim.org/statistics/update.

Note that this utility no longer has an identified use case. This used to be our way of determining which MIMs might 
have out of date PMID references or Orphanet/UMLS mappings, but we've since implemented a way to get these updates 
through the OMIM entry API. 

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
Currently, all of these review cases are part of the "D2G" (Disease-Gene) procesing, and reflect cases where we have 
added associations, but they are strange and need curator review. If the curator decides that an association should not 
be added, an entry for it should be made in [exclusions-disease-gene.tsv](https://github.com/monarch-initiative/omim/blob/main/data/exclusions-disease-gene.tsv).

Columns:
- `classCode`: integer
- `classLabel`: string
- `value`: any: Some form of data to review
- `comment`: string (optional)

#### 1. D2G: digenic
This review case involves what would be otherwise considered a valid, disease-defining disease-gene (D2G) relationship, 
but for the fact  that it quite unusually includes 'digenic' in the label, even though it only had 1 association. OMIM 
doesn't have a guaranatee on the data quality of its disease-gene associations marked 'digenic', so for any of these 
entries, it could  be the case that either (a) it is not 'digenic'; OMIM should remove that from the label, and Mondo 
can make an explicit exception to add the relationship, or could otherwise wait until OMIM fixes the issue and it will 
automatically be added, or (b) it is in fact 'digenic', and OMIM should add the missing 2nd gene association.

#### 2. D2G: self-referential
The unique characteristics of cases of this class are as follows: 
- Each case has 2 rows in `morbidmap.txt` and are part of a pattern. 
- Row 1: One row is a typical, valid, disease-defining entry. For the given phenotype MIM in that row, there are no 
- other rows in `morbidmap.txt` where it appears as a phenotype having an association with another gene.
  - In all such cases seen thus far as of 2024/11/18, all of these are cancer cases, and the label ends with "somatic".
  - This entry appears in the Phenotype-Gene Relationships table on the MIM's omim.org/entry page.
- Row 2: There is a second row where the phenotype in the first row appears as a gene.
  - For this row, there is no MIM in the phenotype field.
  - This row does not appear in the Gene-Phenotype Relationships table on the MIM's omim.org/entry page.
  - This row is self-referential. The label in the Phenotype field is one of the titles of the MIM in the Gene field.

**Example case**:
|Phenotype|Gene/Locus And Other Related Symbols|MIM Number|Cyto Location|
|-|-|-|-|
|Small cell cancer of the lung, somatic, 182280 (3)|RB1|614041|13q14.2|
|Small-cell cancer of lung (2)|SCLC1|182280|3p23-p21|

**All known cases**:
There is a spreadsheet which collates all known cases as of 2024/11/18: [google sheet](
https://docs.google.com/spreadsheets/d/1hKSp2dyKye6y_20NK2HwLsaKNzWfGCMJMP52lKrkHtU/). The MIMs of the known cases are: `159595`, `182280`, `607107`, and `615830`.

**Additional notes**:
Note that unlike the other cases, a single case of "D2G: self-referential" spans multiple rows in `review.tsv`. 
The cases are enumerated in the TSV, with individual cases identifiable via a leading integer in the `value` column, 
e.g. "1: " for the first case, "2: " for the second, and so on.

Also, see note in section "3. D2G: somatic" about intersection between these two cases. 

#### 3. D2G: somatic
Happens when all conditions were met for this association to be considered disease-defining, but the mutation is a somatic cell mutation, rather than a germline mutation. This is indicated by the appearance of the word 'somatic' in the label of the phenotype MIM in the association. These cases should be reviewed because currently any association meeting the criteria to be considered disease-defining is also considered a germline mutation and the association is represented in `omim.owl` using the property 'is causal germline mutation in' (RO:0004013).

Note that there is an intersection between this case and case 2, "D2G: self-referential". Sometimes the somatic cases 
will also be self-referential, but not always. However, all cases of "D2G: self-referential" have historically included 
a row where the phenotype includes the word 'somatic'.

#### 4. D2G: Phenotype is gene
Happens when all conditions were met for this association to be considered disease-defining. However, the phenotype in 
the association unexpectedly has the type of "gene" rather than "phenotype". This is unexpected and considered a data 
quality issue on the OMIM side. As of 2024/10, we flagged this to the OMIM team and they corrected all such cases.

#### 5. D2G: Phenotype type error
Happens when all conditions were met for this association to be considered disease-defining. However, the phenotype in 
the association has an unexpected type of either 'OBSOLETE', 'SUSPECTED', or 'HAS_AFFECTED_FEATURE'. As of 2024/12, we 
have not seen such cases appear, but we have set this review case up to watch for them should they occur.

## Under the hood: Design decisions, etc.
### Gene-Disease processing
Involves the processing of `morbidmap.txt` to create ontological representations of Gene --> Disease and 
Disease --> Gene associations.

#### Example input/output
##### Input: `morbidmap.txt`
| Phenotype                        | Gene/Locus And Other Related Symbols | MIM Number | Cyto Location |
|----------------------------------|--------------------------------------|------------|---------------|
| Prune belly syndrome, 100100 (3) | CHRM3, PBS, EGBRS                    | 118494     | 1q43          |

`OMIM:100100` (Prune belly syndrome) is the Phenotype ("Disease"), and `OMIM:118494` (CHRM3) is the associated Gene. 
They are related via mapping key `(3)` (explained below).

##### Output: `omim.ttl`
```ttl
OMIM:100100 a owl:Class ;
    rdfs:label "prune belly syndrome" ;
    rdfs:subClassOf _:N2fd22c9bb2f04630b81414cff9514660 ;
    biolink:category biolink:Disease .
    
_:N2fd22c9bb2f04630b81414cff9514660 a owl:Restriction ;
    owl:onProperty RO:0004003 ;
    owl:someValuesFrom OMIM:118494 .
```

The association is represented as an `rdfs:subClassOf` `owl:Restriction`, where mapping key `(3)` is represented as 
`RO:0004003`.

#### OMIM MorbidMap mapping keys & Relationship Ontology predicates
In order to add these associations to an OWL ontology, we must use an appropriate predicate. Below are the 4 OMIM 
`morbidmap.txt` mapping keys and [their definitions](https://omim.org/help/faq#1_6), alongside the RO predicates we've 
chosen to represent them.

Note that the directionality of these associations / predicates is in the Gene->Disease direction:
(Gene MIM) --(Mapping key / RO predicate)--> (Disease MIM)

1: The disorder is placed on the map based on its association with a gene, but the underlying defect is not known.  
Not ontologized. These types are ignored due to the uncertainty of the nature of the association.

2: The disorder has been placed on the map by linkage or other statistical method; no mutation has been found.  
[RO:0003303 (causes condition)](https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003303): 
A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure) and a 
condition (a phenotype or disease), where the entity has some causal role for the condition.

3: The molecular basis for the disorder is known; a mutation has been found in the gene.  
[RO:0004013 (is causal germline mutation in)](https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004013): 
Relates a gene to condition, such that a mutation in this gene is sufficient to produce the condition and that can be 
passed on to offspring[modified from orphanet].

Note: For these "mapping key (3)" cases, there also exists an inverse predicate which we ontologize in the 
inverse direction: (Disease MIM) --(Mapping key 3 / RO:0004003)--> (Gene MIM):
[RO:0004003 (has material basis in germline mutation in)](https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004003) 

4: A contiguous gene deletion or duplication syndrome, multiple genes are deleted or duplicated causing the phenotype.  
[RO:0003304 (contributes to condition)](https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003304): 
A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure) and a 
condition (a phenotype or disease), where the entity has some contributing role that influences the condition.

**Important caveat: Singular vs multiple associations**
These above RO predicates are only used if there is only 1 gene associated with a given disease, i.e. 
in `morbidmap.txt`, there is only 1 row where the MIM appears in the `Phenotype` field.

In cases where there is >1 association, the following RO predicate is used instead, regardless of if the mapping key is 
(2), (3), or (4):
[RO:0003302 (causes or contributes to condition)](https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003302): 
A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure) and a 
condition (a phenotype or disease), where the entity has some causal or contributing role that influences the condition.

#### Necessary conditions for disease-defining gene associations
Of the above 3 Gene->Disease association predicates (those with mapping keys (2), (3), and (4)), the one which we 
consider "disease defining" is (3) (RO:0004013). For these cases, as mentioned above, we also declare an association in 
the Disease->Gene direction, RO:0004003. However, we only declare these associations if several other conditions are 
also met. These other conditions are: (i) the Phenotype not be marked as a non-disease (represented by the label 
being wrapped in `[]`), (ii) that is not a mutation that contribute to susceptibility to multifactorial disorders 
(e.g., diabetes, asthma) or to susceptibility to infection (e.g., malaria) (represented by the label being wrapped in 
`{}`), and (iii) not be marked provisional (represented by the label beginning with `?`). These 3 special markers are 
further explained in the [OMIM FAQ](https://omim.org/help/faq#1_6). Additionally, as mentioned above, we only declare 
the association in `omim.ttl` if there is 1 and only 1 association shown in `morbidmap.txt

So, all of the conditions together are:
1. Mapping key is (3)
2. Only 1 association
3. Phenotype not marked as non-disease (`[]`)
4. Phenotype not marked as susceptibility to multifactorial disorders or infection (`{}`)
5. Phenotype not marked provisional (`?`)

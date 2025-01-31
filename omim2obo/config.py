"""Configuration"""
from pathlib import Path
from typing import Optional, TypedDict

import yaml
from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
ENV_PATH = ROOT_DIR / '.env'
REVIEW_CASES_PATH = ROOT_DIR / 'review.tsv'
DISEASE_GENE_EXCLUSIONS_PATH = DATA_DIR / 'exclusions-disease-gene.tsv'
DISEASE_GENE_PROTECTIONS_PATH = DATA_DIR / 'protections-disease-gene.tsv'

with open(DATA_DIR / 'dipper/GLOBAL_TERMS.yaml') as file:
    GLOBAL_TERMS = yaml.safe_load(file)

with open(DATA_DIR / 'dipper/curie_map.yaml') as file:
    CURIE_MAP = yaml.safe_load(file)

CONFIG = dotenv_values(ENV_PATH)

# ReviewCase: See README.md for review class documentation
class ReviewCase(TypedDict):
    """See README.md docs for: review.tsv"""
    classCode: int
    classShortName: str
    value: str
    comment: Optional[str]

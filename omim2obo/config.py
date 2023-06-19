"""Configuration"""
from pathlib import Path
import yaml
from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
ENV_PATH = ROOT_DIR / '.env'

with open(DATA_DIR / 'dipper/GLOBAL_TERMS.yaml') as file:
    GLOBAL_TERMS = yaml.safe_load(file)

with open(DATA_DIR / 'dipper/curie_map.yaml') as file:
    CURIE_MAP = yaml.safe_load(file)

CONFIG = dotenv_values(ENV_PATH)

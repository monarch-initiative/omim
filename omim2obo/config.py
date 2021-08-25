from pathlib import Path
import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'

with open(DATA_DIR / 'dipper/GLOBAL_TERMS.yaml') as file:
    GLOBAL_TERMS = yaml.safe_load(file)

with open(DATA_DIR / 'dipper/curie_map.yaml') as file:
    CURIE_MAP = yaml.safe_load(file)

config = dotenv_values(ROOT / '.env')

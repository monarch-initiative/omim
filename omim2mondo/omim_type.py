from enum import Enum
from namespaces import *


class OmimType(Enum):
    OBSOLETE = HP['0031859']  # Caret
    GENE = SO['0000704']  # Asterist
    SUSPECTED = NCIT.C71458  # NULL
    PHENOTYPE = UPHENO['0001001']  # Number Sign
    HERITABLE_PHENOTYPIC_MARKER = SO['0001500']  # Percent
    HAS_AFFECTED_FEATURE = GENO['0000418']  # Plus

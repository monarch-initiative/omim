"""OMIM Types"""
from enum import Enum
from omim2obo.namespaces import *


class OmimType(Enum):
    """From OMIM docs: What do the symbols preceding a MIM number represent?

    *: An asterisk (*) before an entry number indicates a **gene**.

    #: A number symbol (#) before an entry number indicates that it is a **descriptive**
    entry, usually of a phenotype, and does not represent a unique locus. The
    reason for the use of the number symbol is given in the first paragraph of
    the entry. Discussion of any gene(s) related to the phenotype resides in
    another entry(ies) as described in the first paragraph.

    +: A plus sign (+) before an entry number indicates that the entry contains the
    description of a gene of known **sequence** and a **phenotype**.

    %: A percent sign (%) before an entry number indicates that the entry describes
    a confirmed mendelian **phenotype** or phenotypic locus for which the underlying
    molecular basis is not known.

    '': No symbol before an entry number generally indicates a **description** of a phenotype
    for which the mendelian basis, although suspected, has not been clearly established
    or that the separateness of this phenotype from that in another entry is unclear.

    ^: A caret (^) before an entry number means the entry no longer exists because
    it was **removed** from the database or moved to another entry as indicated.

    See also the description of symbols used in the disorder column of the OMIM
    Gene Map and Morbid Map."""
    OBSOLETE = HP['0031859']  # Caret ^
    GENE = SO['0000704']  # Asterisk *
    SUSPECTED = NCIT.C71458  # NULL
    PHENOTYPE = UPHENO['0001001']  # Number Sign #
    HERITABLE_PHENOTYPIC_MARKER = SO['0001500']  # Percent %
    HAS_AFFECTED_FEATURE = GENO['0000418']  # Plus +


OMIM_PREFIX = {
    '^': HP['0031859'],
    '*': SO['0000704'],
    '#': UPHENO['0001001'],
    '%': SO['0001500'],
    '+': GENO['0000418'],
    None: NCIT.C71458
}


def get_omim_type(prefix):
    """Return OMIM type from OMIM prefix map"""
    return OMIM_PREFIX[prefix]

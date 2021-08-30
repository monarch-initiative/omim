import re

from omim2obo.namespaces import PMID, ORPHANET, UMLS
from omim2obo.utils.romanplus import *
from pathlib import Path
from typing import List, Dict
from rdflib import Namespace
from collections import defaultdict


def check_version(file_path):
    print(Path(file_path).stat())


def cleanup_synonym(synonym):
    """
    Reformat to lower case the first character of the string.

    :param synonym: str
    :return: str
    """
    abbrev_with_periods = re.match('^([A-Z]\.){2,}$', synonym)
    abbrev_without_periods = re.match('^[A-Z]{2,}$', synonym)
    if abbrev_with_periods or abbrev_without_periods:
        return synonym
    else:
        return synonym[0].lower() + synonym[1:]


def cleanup_label(label):
    """
    Reformat the ALL CAPS OMIM labels to something more pleasant to read.
    This will:
    1.  remove the abbreviation suffixes
    2.  convert the roman numerals to integer numbers
    3.  make the text title case, w/ exceptions for
        - supplied conjunctions/prepositions/articles
        - the first character of the string
    :param label: str
    :return: str
    """
    conjunctions = ['and', 'but', 'yet', 'for', 'nor', 'so']
    little_preps = [
        'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'it', 'or']
    articles = ['a', 'an', 'the']

    # remove the abbreviation
    lbl = label.split(r';')[0]

    fixedwords = []
    i = 0
    for wrd in lbl.split():
        i += 1
        # convert the roman numerals to numbers,
        # but assume that the first word is not
        # a roman numeral (this permits things like "X inactivation"
        if i > 1 and re.match(romanNumeralPattern, wrd):
            num = fromRoman(wrd)
            # make the assumption that the number of syndromes are <100
            # this allows me to retain "SYNDROME C"
            # and not convert it to "SYNDROME 100"
            if 0 < num < 100:
                # get the non-roman suffix, if present.
                # for example, IIIB or IVA
                suffix = wrd.replace(toRoman(num), '', 1)
                fixed = ''.join((str(num), suffix))
                wrd = fixed

        # capitalize first letter, except for first word
        if i > 1:
            wrd = wrd.title()

        # replace interior conjunctions, prepositions,
        # and articles with lowercase
        if wrd.lower() in (conjunctions + little_preps + articles) and i != 1:
            wrd = wrd.lower()

        fixedwords.append(wrd)

    lbl = ' '.join(fixedwords)

    # print (label, '-->', lbl)
    return lbl


def get_alt_labels(titles):
    """
    From a string of delimited titles, make an array.
    This assumes that the titles are double-semicolon (';;') delimited.
    This will additionally pass each through the _cleanup_label method to
    convert the screaming ALL CAPS to something more pleasant to read.
    :param titles:
    :return: an array of cleaned-up labels
    """

    labels = []
    # "alternativeTitles": "
    #   ACROCEPHALOSYNDACTYLY, TYPE V; ACS5;;\nACS V;;\nNOACK SYNDROME",
    # "includedTitles":
    #   "CRANIOFACIAL-SKELETAL-DERMATOLOGIC DYSPLASIA, INCLUDED"

    for title in titles.split(';;'):
        # remove ', included', if present
        label = re.sub(r',\s*INCLUDED', '', title.strip(), re.IGNORECASE)
        label = cleanup_label(label)
        labels.append(label)

    return labels


def get_mapped_gene_ids(entry) -> List[str]:
    gene_ids = entry.get('externalLinks', {}).get('geneIDs', '')
    return [s.strip() for s in gene_ids.split(',')]
    # omim_num = str(entry['mimNumber'])
    # omim_curie = 'OMIM:' + omim_num
    # if 'externalLinks' in entry:
    #     links = entry['externalLinks']
    #     omimtype = omim_type[omim_num]
    #     if 'geneIDs' in links:
    #         entrez_mappings = links['geneIDs']
    #         gene_ids = entrez_mappings.split(',')
    #         omim_ncbigene_idmap[omim_curie] = gene_ids
    #         if omimtype in [
    #                 globaltt['gene'], self.globaltt['has_affected_feature']]:
    #             for ncbi in gene_ids:
    #                 model.addEquivalentClass(omim_curie, 'NCBIGene:' + str(ncbi))
    # return gene_ids


def get_pubs(entry) -> List[str]:
    result = []
    for rlst in entry.get('referenceList', []):
        if 'pubmedID' in rlst['reference']:
            result.append(str(rlst['reference']['pubmedID']))
    return result


def get_mapped_ids(entry) -> Dict[Namespace, List[str]]:
    external_links = entry.get('externalLinks', {})
    result = defaultdict(list)
    if 'orphanetDiseases' in external_links:
        for item in external_links['orphanetDiseases'].strip().split(';;;'):
            result[ORPHANET].append(item.split(';;')[0].strip())
    if 'umlsIDs' in external_links:
        result[UMLS] = external_links['umlsIDs'].split(',')
    return result


def get_phenotypic_series(entry) -> List[str]:
    result = []
    for pheno in entry.get('phenotypeMapList', []):
        if 'phenotypicSeriesNumber' in pheno['phenotypeMap']:
            result.extend(pheno['phenotypeMap']['phenotypicSeriesNumber'].split(','))
    for pheno in entry.get('geneMap', {}).get('phenotypeMapList', []):
        if 'phenotypicSeriesNumber' in pheno['phenotypeMap']:
            result.extend(pheno['phenotypeMap']['phenotypicSeriesNumber'].split(','))
    return list(set(result))


def get_process_allelic_variants(entry) -> List:
    return []

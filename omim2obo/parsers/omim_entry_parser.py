"""OMIM Entry parsers"""
import csv
import logging
# import re
from collections import defaultdict
from copy import copy
from typing import List, Dict, Set, Tuple, Union

import pandas as pd
from rdflib import Graph, RDF, RDFS, DC, Literal, OWL, SKOS, URIRef
# from rdflib import Namespace

from omim2obo.config import DATA_DIR
from omim2obo.omim_type import OmimType, get_omim_type
from omim2obo.namespaces import *
from omim2obo.utils.romanplus import *


LOG = logging.getLogger('omim2obo.parsers.api_entry_parser')


def get_known_capitalizations() -> Dict[str, str]:
    """Get list of known capitalizations for proper names, acronyms, and the like.
    todo: Contains space-delimited words, e.g. "vitamin d". The way that
     cleanup_label is currently implemented, each word in the label gets
     replaced; i.e. it would try to replace "vitamin" and "d" separately. Hence,
     this would fail.
     Therefore, we should probably do this in 2 different operations: (1) use
     the current 'word replacement' logic, but also, (2), at the end, do a
     generic string replacement (e.g. my_str.replace(a, b). When implementing
     (2), we should also split this dictionary into two separate dictionaries,
     each for 1 of these 2 different purposes.

    todo: known_capitalizations.tsv can be refactored possibly. It really only needs 1 column, the case to replaace. The
     pattern column is not used, and the first column (lowercase) can be computed by using .lower() on the case to
     replace. We could also leave as-is since this file is shared elsewhere in the project infrastructure, though I do
     not know its source-of-truth location.
    """
    path = DATA_DIR / 'known_capitalizations.tsv'
    with open(path, "r") as file:
        data_io = csv.reader(file, delimiter="\t")
        data: List[List[str]] = [x for x in data_io]
    df = pd.DataFrame(data[1:], columns=data[0])
    d = {}
    for index, row in df.iterrows():
        d[row['lower_name']] = row['cap_name']
    return d


CAPITALIZATION_REPLACEMENTS: Dict[str, str] = get_known_capitalizations()


# todo: This isn't used in the ingest to create omim.ttl. Did this have some other use case?
def transform_entry(entry) -> Graph:
    """
    Transforms an OMIM API entry to a graph.
    This function is obsolete and incomplete. It should only be used to verify the API entry and some functions

    :param entry:
    :return:
    """
    omim_type = get_omim_type(entry.get('prefix', None))
    omim_num = str(entry['mimNumber'])
    titles = entry['titles']
    label = titles['preferredTitle']

    graph = Graph()

    omim_uri = URIRef(OMIM[omim_num])
    other_labels = []
    if 'alternativeTitles' in titles:
        cleaned, label_endswith_included = parse_title_symbol_pairs(titles['alternativeTitles'])
        other_labels += cleaned
    if 'includedTitles' in titles:
        cleaned, label_endswith_included = parse_title_symbol_pairs(titles['includedTitles'])
        other_labels += cleaned

    graph.add((omim_uri, RDF.type, OWL.Class))

    abbrev = label.split(';')[1].strip() if ';' in label else None

    if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER.value:  # %
        graph.add((omim_uri, RDFS.label, Literal(cleanup_title(label))))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
    elif omim_type == OmimType.GENE.value or omim_type == OmimType.HAS_AFFECTED_FEATURE.value:  # * or +
        omim_type = OmimType.GENE.value
        graph.add((omim_uri, RDFS.label, Literal(abbrev)))
        graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
    elif omim_type == OmimType.PHENOTYPE.value:  # #
        graph.add((omim_uri, RDFS.label, Literal(cleanup_title(label))))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
    else:  # ^ or NULL (no prefix character)
        graph.add((omim_uri, RDFS.label, Literal(cleanup_title(label))))

    graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label)))
    for label in other_labels:
        graph.add((omim_uri, oboInOwl.hasRelatedSynonym, Literal(label)))

    if 'geneMapExists' in entry and entry['geneMapExists']:
        genemap = entry['geneMap']
        is_gene = False
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER.value:  # %
            ncbi_ids = get_mapped_gene_ids(entry)
            if len(ncbi_ids) > 0:
                feature_uri = NCBIGENE[ncbi_ids[0]]
            for ncbi_id in ncbi_ids:
                # TODO: This might need to be bnodes
                # MONARCH:b10cbd376598f2d328ff a OBAN:association ;
                #     OBAN:association_has_object OMIM:100070 ;
                #     OBAN:association_has_predicate RO:0002200 ;
                #     OBAN:association_has_subject NCBIGene:100329167 .
                graph.add((NCBIGENE[ncbi_id.strip()], RO['0002200'], omim_uri))
        elif omim_type == OmimType.GENE.value or omim_type == OmimType.HAS_AFFECTED_FEATURE.value:  # * or +
            feature_uri = omim_uri
            is_gene = True

        if feature_uri is not None:
            if 'comments' in genemap:
                comments = genemap['comments']
                if comments.strip():
                    graph.add((feature_uri, DC.description, Literal(comments)))
            if 'cytoLocation' in genemap:
                cytoloc = genemap['cytoLocation']
                tax_id = '9606'
                chr_id = tax_id + 'chr' + cytoloc
                graph.add((feature_uri, RO['0002525'], CHR[chr_id]))

    # Pubmed Citations
    for pmid in get_pubs(entry):
        graph.add((omim_uri, IAO['0000142'], PMID[pmid]))

    # Mapped IDs
    for namespace, mapped_ids in get_mapped_ids(entry).items():
        for mapped_id in mapped_ids:
            graph.add((omim_uri, SKOS.exactMatch, namespace[mapped_id]))

    # Phenotypic series
    for phenotypic_serie in get_phenotypic_series(entry):
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER.value or omim_type == OmimType.PHENOTYPE.value:
            graph.add((omim_uri, RDFS.subClassOf, OMIMPS[phenotypic_serie]))
        elif omim_type == OmimType.GENE.vaule or omim_type == OmimType.HAS_AFFECTED_FEATURE.value:
            graph.add((omim_uri, RO['0003304'], OMIMPS[phenotypic_serie]))

    # NCBI ENTREZ Gene IDs
    if omim_type == OmimType.GENE.value or omim_type ==  OmimType.HAS_AFFECTED_FEATURE.value:
        for gene_id in get_mapped_gene_ids(entry):
            graph.add((omim_uri, OWL.equivalentClass, NCBIGENE[gene_id]))

    # Allelic Variants
    for allelic_variant in get_process_allelic_variants(entry):
        ...
    return graph


def detect_abbreviations(label: str, capitalization_threshold=0.75) -> List[str]:
    """Detect possible abbreviations / acronyms"""
    # Compile regexp
    acronyms_without_periods_compiler = re.compile('[A-Z]{1}[A-Z0-9]{1,}')
    acronyms_with_periods_compiler = re.compile('[A-Z]{1}\.([A-Z0-9]\.){1,}')
    title_cased_abbrev_compiler = re.compile('[A-Z]{1}[a-zA-Z]{1,}\.')

    # Special threshold-based logic, because incoming data has highly inconsistent capitalization
    # is_largely_uppercase = synonym.upper() == synonym  # too many false positives
    fully_capitalized_count = 0
    words = label.split()
    for word in words:
        if word.upper() == word:
            fully_capitalized_count += 1
    is_largely_uppercase = \
        fully_capitalized_count / len(words) >= capitalization_threshold

    # Detect cases
    if is_largely_uppercase:
        acronyms_without_periods = []  # can't infer because everything was uppercase
    else:
        acronyms_without_periods: List[str] = acronyms_without_periods_compiler.findall(label)
    title_cased_abbrevs: List[str] = title_cased_abbrev_compiler.findall(label)
    acronyms_with_periods: List[str] = acronyms_with_periods_compiler.findall(label)

    return acronyms_with_periods + acronyms_without_periods + title_cased_abbrevs


# todo: rename? It's doing more than cleaning; it's mutating
def cleanup_title(
    title: str,
    replacement_case_method: str = 'lower',  # 'upper', 'title', 'lower', 'capitalize' (=sentence case)
    conjunctions: List[str] = ['and', 'but', 'yet', 'for', 'nor', 'so'],
    little_preps: List[str] = ['at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'it', 'or'],
    articles: List[str] = ['a', 'an', 'the'],
    word_replacements: Dict[str, str] = CAPITALIZATION_REPLACEMENTS,
) -> str:
    """Reformat the ALL CAPS OMIM labels to something more pleasant to read.

    :param title: A preferred, alternative, or included title.

    1. Converts roman numerals to arabic
    2. Makes the text adhere to the case of `replacement_case_method`, except for supplied
    conjunctions, prepositions, and articles, which will always be lowercased. NOTE: The default for this is 'lower',
    meaning that this operation by default does nothing.

    Assumptions:
    1. All acronyms are capitalized

    todo later's:
    1: Find a pattern for hyphenated types, and maintain acronym capitalization
       e.g. MITF-related melanoma and renal cell carcinoma predisposition syndrome
       e.g. ATP1A3-associated neurological disorder
    2. Make pattern for chromosomes
       agonadism, 46,XY, with intellectual disability, short stature, retarded bone age, and multiple extragenital
         malformations
       Chromosome special formatting capitalization?
       There seems to be special formatting for chromosome refs; they have a comma in the middle, but with no space
       after the comma, though some places I saw on the internet contained a space.
       e.g. "46,XY" in: agonadism, 46,XY, with intellectual disability, short stature, retarded bone age, and multiple
         extragenital malformations
    3. How to find acronym if it is capitalized but only includes char [A-Z], and
        every other char in the string is also capitalized? I don't see a way unless
        checking every word against an explicit dictionary of terms, though there are sure
        to also be (i) acronyms in that dictionary, and (ii) non-acronyms missing from
        that dictionary. And also concern (iii), where to get such an extensive dictionary?
    4. Add "special character" inclusion into acronym regexp. But which special
        chars to include, and which not to include?
    5. Acronym capture extension: case where at least 1 word is not capitalized:
        any word that is fully capitalized might as well be acronym, so long
       as at least 1 other word in the label is not all caps. Maybe not a good rule,
       because there could be some violations, and this probably would not happen
       that often anwyay
        - Not sure what I meant about (5) - joeflack4 2021/09/10
    6. Eponyms: re-capitalize first char?
       e.g.: Balint syndrome, Barre-Lieou syndrome, Wallerian degeneration, etc.
       How to do this? Simply get/create a list of known eponyms? Is this feasible?
    """
    fixedwords = []
    i = 0
    for wrd in title.split():
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
        wrd = getattr(wrd, replacement_case_method)()
        # replace interior conjunctions, prepositions, and articles with lowercase, always
        if wrd in (conjunctions + little_preps + articles) and i != 1:
            wrd = wrd.lower()
        if word_replacements:
            wrd = word_replacements.get(wrd, wrd)
        fixedwords.append(wrd)
    label_newcase = ' '.join(fixedwords)

    return label_newcase


def recapitalize_acronyms_in_title(title: str, known_abbrevs: Set[str] = None, capitalization_threshold=0.75) -> str:
    """Re-capitalize acronyms / words based on information contained w/in original label

    todo: If title has been used on cleanup_title() using a replacement_case_method other than the non-default 'lower',
     then the .replace() operation will not work. To solve, this (a) capture the replacement_case_method used and
     pass that here, or (b) duplicate the .replace() line and call it on alternative casing variations (.title() and
     capitalize() (=sentence case)), (c) possibly just compare to word.lower() instead of 'word.
    todo: (more important): It's probable that .split(' ') is not enough to cover all cases. Should also run the check
     by splitting on other characters. E.g. consider the following potential cases: "TITLE (ACRONYM)",
     "TITLE: ACRONYM1&ACRONYM2", "TITLE/ACRONYM" or "TITLE ACRONYM/ACRONYM", "TITLE {ACRONYM1,ACRONYM2}",
     "TITLE[ACRONYM]",  "TITLE-ACRONYM", or less likely cases such as "TITLE_ACRONYM", "TITLE.ACRONYM". There are quite
      a few different combos of special char usage that could theoretically arise. It might be possible for thisthat to
      utilize the regular expressions in detect_abbreviations(), and substitute in the acronym in the place of the [A-Z]
      part. It is also possible to improve detect_abbreviations() by considering some of thes eother possible example
      cases above.
    """
    inferred_abbrevs: Set[str] = set(detect_abbreviations(title, capitalization_threshold))
    abbrevs: Set[str] = known_abbrevs.union(inferred_abbrevs)
    if not abbrevs:
        return title
    title2_words: List[str] = []
    for word in title.split():
        abbrev_match = False
        for abbrev in abbrevs:
            if abbrev.lower() == word:
                title2_words.append(abbrev)
                abbrev_match = True
                break
        if not abbrev_match:
            title2_words.append(word)
    title2 = ' '.join(title2_words)
    return title2


def recapitalize_acronyms_in_titles(
    titles: Union[str, List[str]], known_abbrevs: Set[str] = None, capitalization_threshold=0.75
) -> Union[str, List[str]]:
    """Re-capitalize acronyms in a list of titles"""
    if isinstance(titles, str):
        return recapitalize_acronyms_in_title(titles, known_abbrevs, capitalization_threshold)
    return [recapitalize_acronyms_in_title(title, known_abbrevs, capitalization_threshold) for title in titles]


def remove_included_and_formerly_suffixes(title: str) -> str:
    """Remove ', INCLUDED' and ', FORMERLY' suffixes from a title"""
    for suffix in ['FORMERLY', 'INCLUDED']:
        title = re.sub(r',\s*' + suffix, '', title, re.IGNORECASE)
    return title


def separate_former_titles_and_symbols(
    titles: List[str], symbols: List[str]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Separate current title/symbols from deprecated (marked 'former') ones"""
    former_titles = [x for x in titles if ', FORMERLY' in x.upper()]
    former_symbols = [x for x in symbols if ', FORMERLY' in x.upper()]
    current_titles = [x for x in titles if ', FORMERLY' not in x.upper()]
    current_symbols = [x for x in symbols if ', FORMERLY' not in x.upper()]
    return current_titles, current_symbols, former_titles, former_symbols


def clean_alt_and_included_titles(titles: List[str], symbols: List[str]) -> Tuple[List[str], List[str]]:
    """Remove ', INCLUDED' and ', FORMERLY' suffixes from titles/symbols & misc title reformatting"""
    # remove ', included' and ', formerly', if present
    titles2 = [remove_included_and_formerly_suffixes(x) for x in titles]
    symbols2 = [remove_included_and_formerly_suffixes(x) for x in symbols]
    # additional reformatting for titles
    titles3 = [cleanup_title(x) for x in titles2]
    return titles3, symbols2


def parse_title_symbol_pairs(title_symbol_pairs_str: str) -> Tuple[List[str], List[str]]:
    """Parses a string containing title-symbol pairs.

    :param title_symbol_pairs_str: A string representing title-symbol pairs.
    Format:
    - Pairs are separated by ';;'
    - Within each pair:
        - The first element is always a title
        - Optionally followed by zero or more symbols, separated by ';'

    Examples:
      Positional semantics:
        Title1;Symbol1;Symbol2;;Title2;;Title3;Symbol3
      Alternative Title(s); symbol(s):
        ACROCEPHALOSYNDACTYLY, TYPE V; ACS5;; ACS V;; NOACK SYNDROME
      Included Title(s); symbols:
        CRANIOFACIAL-SKELETAL-DERMATOLOGIC DYSPLASIA, INCLUDED
    """
    titles: List[str] = []
    symbols: List[str] = []
    title_symbol_pairs: List[str] = title_symbol_pairs_str.split(';;')
    for pair_str in title_symbol_pairs:
        pair: List[str] = [x.strip() for x in pair_str.split(';')]
        titles.append(pair[0])
        symbols.extend(pair[1:])
    return titles, symbols


def get_alt_and_included_titles_and_symbols(title_symbol_pair_str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Separates different types of titles/symbols, and cleans them."""
    titles: List[str] = []
    symbols: List[str] = []
    former_titles: List[str] = []
    former_symbols: List[str] = []
    if title_symbol_pair_str:
        titles, symbols = parse_title_symbol_pairs(title_symbol_pair_str)
        titles, symbols, former_titles, former_symbols = separate_former_titles_and_symbols(titles, symbols)
        titles, symbols = clean_alt_and_included_titles(titles, symbols)
        former_titles, former_symbols = clean_alt_and_included_titles(former_titles, former_symbols)
    return titles, symbols, former_titles, former_symbols


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


# noinspection PyUnusedLocal
def get_process_allelic_variants(entry) -> List:
    # Not sure when/if Dazhi intended to use this - joeflack4 2021/12/20
    return []

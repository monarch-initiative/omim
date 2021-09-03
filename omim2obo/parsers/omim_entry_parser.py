import logging
from typing import Optional
from rdflib import Graph, Namespace, RDF, RDFS, DC, Literal, OWL, URIRef
from typing import List, Dict
from rdflib import Namespace
from collections import defaultdict
import re
from omim2obo.omim_type import OmimType, get_omim_type
from omim2obo.namespaces import *
from omim2obo.utils.romanplus import *

LOG = logging.getLogger('omim2obo.parsers.api_entry_parser')


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
        other_labels += get_alt_labels(titles['alternativeTitles'])
    if 'includedTitles' in titles:
        other_labels += get_alt_labels(titles['includedTitles'])

    graph.add((omim_uri, RDF.type, OWL.Class))

    abbrev = label.split(';')[1].strip() if ';' in label else None

    if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER.value:  # %
        graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
    elif omim_type == OmimType.GENE.value or omim_type == OmimType.HAS_AFFECTED_FEATURE.value:  # * or +
        omim_type = OmimType.GENE.value
        graph.add((omim_uri, RDFS.label, Literal(abbrev)))
        graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
    elif omim_type == OmimType.PHENOTYPE.value:  # #
        graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))
        graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
    else:
        graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))

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
            graph.add((omim_uri, oboInOwl.hasDbXref, namespace[mapped_id]))

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


def cleanup_label(label):
    """
    Reformat the ALL CAPS OMIM labels to something more pleasant to read.
    This will:
    1.  remove the abbreviation suffixes
    2.  convert the roman numerals to integer numbers
    3.  make the text title case,
        except for suplied conjunctions/prepositions/articles
    :param label:
    :return:
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

        # capitalize first letter
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

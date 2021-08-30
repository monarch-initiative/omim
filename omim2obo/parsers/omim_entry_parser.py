import logging
from typing import Optional
from rdflib import Graph, Namespace, RDF, RDFS, DC, Literal, OWL, URIRef

from omim2obo.main import OmimGraph
from omim2obo.omim_type import OmimType, get_omim_type
from omim2obo.utils.api_entry import cleanup_label, get_mapped_gene_ids, get_pubs, get_mapped_ids, get_phenotypic_series, \
    get_process_allelic_variants, get_alt_labels
from omim2obo.namespaces import *

LOG = logging.getLogger('omim2obo.parsers.api_entry_parser')


def transform_entry(entry) -> Graph:
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

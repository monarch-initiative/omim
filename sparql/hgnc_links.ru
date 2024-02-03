PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix IAO: <http://purl.obolibrary.org/obo/IAO_>
prefix MONDO: <http://purl.obolibrary.org/obo/MONDO_>
prefix RO: <http://purl.obolibrary.org/obo/RO_>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix oio: <http://www.geneontology.org/formats/oboInOwl#>
prefix def: <http://purl.obolibrary.org/obo/IAO_0000115>
prefix owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

INSERT {
    ?hgnc rdf:type owl:Class .
    ?cls rdfs:subClassOf [
        owl:onProperty RO:0004003 ;
        owl:someValuesFrom ?hgnc
    ] .
}

WHERE
{
  ?cls a owl:Class .
  ?cls rdfs:subClassOf [
        owl:onProperty RO:0004003 ;
        owl:someValuesFrom ?omim_gene
      ] .
    ?omim_gene skos:exactMatch ?hgnc .
    FILTER(STRSTARTS(STR(?hgnc), "http://identifiers.org/hgnc/"))
}

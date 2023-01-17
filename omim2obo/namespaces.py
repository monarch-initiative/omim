from rdflib import Namespace

MONARCH = Namespace('https://monarchinitiative.org/MONARCH_')                 # local BOGUS IRI effectivly bnodes but less
BNODE = Namespace('https://monarchinitiative.org/.well-known/genid/')         # local RDF Skolemized Blank Node

MONARCHDATA = Namespace('https://data.monarchinitiative.org/ttl/')            # Bleeding edge RDF data
MONARCHARCHIVE = Namespace('https://archive.monarchinitiative.org/')          # Release RDF data
MONARCHLOGOREPO = Namespace('https://github.com/monarch-initiative/monarch-ui/blob/master/public/img/sources/')  # Monarch')s stash of logos for sources we ingest - this is used to set schemalogo in Dataset.py

BIOLINK = Namespace('https://w3id.org/biolink/vocab/')                         # Biolink model
#

# ontologies

AQTLTRAIT = Namespace('http://identifiers.org/animalqtltrait/')               # Animal Quantitative Trait Loci Database
# FIXME - should get integrated into Upheno

BFO = Namespace('http://purl.obolibrary.org/obo/BFO_')                        # Basic Formal Ontology
COHD = Namespace('http://purl.obolibrary.org/obo/COHD_')                      # Columbia Open Health Data
CHEBI = Namespace('http://purl.obolibrary.org/obo/CHEBI_')                    # Chemicals of Biological Interest
CHR = Namespace('http://purl.obolibrary.org/obo/CHR_')                        # Chromosome Ontology
CL = Namespace('http://purl.obolibrary.org/obo/CL_')                          # Cell Ontology (cell types)
CLO = Namespace('http://purl.obolibrary.org/obo/CLO_')                        # Cell Line Ontology
CMO = Namespace('http://purl.obolibrary.org/obo/CMO_')                        # Clinical Measurements Ontology
EDAM_DATA = Namespace('http://edamontology.org/data_')                        # Data and Methods Ontology (data artifacts)
DC_CL = Namespace('http://purl.obolibrary.org/obo/DC_CL')                     #  *** seeing it fixed in github but not yet live was `DC`
DECIPHER = Namespace('https://decipher.sanger.ac.uk/syndrome/')               # Deciphering Developmental Disease
DOID = Namespace('http://purl.obolibrary.org/obo/DOID_')                      # Human Disease Ontology
ECO = Namespace('http://purl.obolibrary.org/obo/ECO_')                        # Evidence Code Ontology
EFO = Namespace('http://www.ebi.ac.uk/efo/EFO_')                              # Experimental Factor Ontology (all kinds of stuff)
ENVO = Namespace('http://purl.obolibrary.org/obo/ENVO_')                      # Environment Ontology
ERO = Namespace('http://purl.obolibrary.org/obo/ERO_')                        # Eeagle-i Resource Ontology
FALDO = Namespace('http://biohackathon.org/resource/faldo#')                  # Feature Annotation Location Description Ontology
FBCV = Namespace('http://purl.obolibrary.org/obo/FBcv_')                      # FlyBase Controled Vocabulary (includes phenotypes)
FBBT = Namespace('http://purl.obolibrary.org/obo/FBbt_')                      # FlyBase anatomy
FBDV = Namespace('http://purl.obolibrary.org/obo/FBdv_')                      # Flybase developmental stages
# till we get a purl? `FBgn': 'http://flybase.org/reports/'         # flybase gene?
GARD = Namespace('http://purl.obolibrary.org/obo/GARD_')                      # Genetic and Rare Diseases (GARD) Information Center
GENO = Namespace('http://purl.obolibrary.org/obo/GENO_')                      # Genotype Partonomy Ontology
GO = Namespace('http://purl.obolibrary.org/obo/GO_')                          # Gene Ontology
HP = Namespace('http://purl.obolibrary.org/obo/HP_')                          # Human Phenotype Ontology
IAO = Namespace('http://purl.obolibrary.org/obo/IAO_')                        # Information Artifact Ontology
ICD9 = Namespace('http://purl.obolibrary.org/obo/ICD9_')                      # International Classification of Disease 9th Rev
KEGG_DS = Namespace('http://purl.obolibrary.org/KEGG-ds_')                    # Kyoto Encyclopedia of Genes and Genomes Disease Ontology
LPT = Namespace('http://purl.obolibrary.org/obo/LPT_')                        # Livestock Phenotypic Trait Ontology
MA = Namespace('http://purl.obolibrary.org/obo/MA_')                          # Mouse Anatomy Ontology
MEDGEN = Namespace('http://www.ncbi.nlm.nih.gov/medgen/')                     # Human Medical Genetics vocabulary
MESH = Namespace('http://id.nlm.nih.gov/mesh/')                               # Medical Subject Headings (medical diseases, phenotypes, and drugs)
MP = Namespace('http://purl.obolibrary.org/obo/MP_')                          # Mammalian Phenotype Ontology
MPATH = Namespace('http://purl.obolibrary.org/obo/MPATH_')                    # Mammalian Pathology Ontology
NBO = Namespace('http://purl.obolibrary.org/obo/NBO_')                        # NeuroBehavior Ontology
OBA = Namespace('http://purl.obolibrary.org/obo/OBA_')                        # Ontology of Biological Attributes (traits)
OBAN = Namespace('http://purl.org/oban/')                                     # Open Biomedical Annotation Model
OBI = Namespace('http://purl.obolibrary.org/obo/OBI_')                        # Ontology of Biomedical Investigations
OBO = Namespace('http://purl.obolibrary.org/obo/')                            # Biological Ontology namespace (this is not itself an ontology)
OBOINOWL = Namespace('http://www.geneontology.org/formats/oboInOwl#')         # obo-specific annotation properties, like synonym types
# 'OMIA' was http://omia.angis.org.au/ IS https://omia.org/         # (see about helping to update original data)
OMIA = Namespace('https://omia.org/OMIA')                                     # Online Mendelian Inheritance in Animals (disease/species)
# LIDIA seems retired. so these are not resovable                   # Also: http://www.vetsci.usyd.edu.au/lida/
LIDA = Namespace('http://sydney.edu.au/vetscience/lida/dogs/search/disorder/')  # Listing of Inherited Disorders in Animals (defunct?)
OMIM = Namespace('https://omim.org/entry/')                                    # Online Mendelian Inheritance in Man (human disease and variants)
OMIMPS = Namespace('https://www.omim.org/phenotypicSeries/PS')                   # Online Mendelian Inheritance in Man (phenotypes)
ORPHA = Namespace('http://www.orpha.net/ORDO/Orphanet_')                      # Rare diseases and Orphan drugs
PATO = Namespace('http://purl.obolibrary.org/obo/PATO_')                      # Phenotypic Quality Ontology
PCO = Namespace('http://purl.obolibrary.org/obo/PCO_')                        # Population and Community Ontology
PR = Namespace('http://purl.obolibrary.org/obo/PR_')                          # Protein ontology
PW = Namespace('http://purl.obolibrary.org/obo/PW_')                          # PathWay ontology
RO = Namespace('http://purl.obolibrary.org/obo/RO_')                          # Relationship Ontology
SCTID = Namespace('http://purl.obolibrary.org/obo/SCTID_')                    # SNOMED
SIO = Namespace('http://semanticscience.org/resource/SIO_')                   # SemanticScience Integrated Ontology (information artifacts)
SNOMED = Namespace('http://purl.obolibrary.org/obo/SNOMED_')                  # Diseases and Phenotypes
SO = Namespace('http://purl.obolibrary.org/obo/SO_')                          # Sequence Ontology
STATO = Namespace('http://purl.obolibrary.org/obo/STATO_')                    # Statistics Ontology
UBERON = Namespace('http://purl.obolibrary.org/obo/UBERON_')                  # Integrated anatomy ontology (metazoans, mostly)
UPHENO = Namespace('http://purl.obolibrary.org/obo/UPHENO_')                  # Integrated phenotype ontology, and normal traits
UMLS = Namespace('http://linkedlifedata.com/resource/umls/id/')               # Unified Medical Language system
UO = Namespace('http://purl.obolibrary.org/obo/UO_')                          # Units of measurements
VT = Namespace('http://purl.obolibrary.org/obo/VT_')                          # Vertebrate Trait Ontology
WBPHENOTYPE = Namespace('http://purl.obolibrary.org/obo/WBPhenotype_')        # WormBase Phenotypes (nematode)
XCO = Namespace('http://purl.obolibrary.org/obo/XCO_')                        # Experimental Conditions Ontology
ZFA = Namespace('http://purl.obolibrary.org/obo/ZFA_')                        # Zebrafish Anatomy Ontology
ZFS = Namespace('http://purl.obolibrary.org/obo/ZFS_')                        # Zebrafish Staging
ZP = Namespace('http://purl.obolibrary.org/obo/ZP_')                          # Zebrafish Phenotype Ontology
WBBT = Namespace('http://purl.obolibrary.org/obo/WBbt_')                      # C. elegans gross anatomy
EMAPA = Namespace('http://purl.obolibrary.org/obo/EMAPA_')                    # Mouse gross anatomy and development, timed
XAO = Namespace('http://purl.obolibrary.org/obo/XAO_')                        # Xenopus Anatomy and development
MONDO = Namespace('http://purl.obolibrary.org/obo/MONDO_')                    # Monarch Disease Ontology
NCIT = Namespace('http://purl.obolibrary.org/obo/NCIT_')                      # National Cancer Institute Thesaurus
SEPIO = Namespace('http://purl.obolibrary.org/obo/SEPIO_')                    # Scientific Evidence and Provenance Information Ontology
VIVO = Namespace('http://vivoweb.org/ontology/core#')                         # ontology for representing scholarship
VFB = Namespace('http://virtualflybrain.org/reports/')                        # Drosophila neuroanatomy


# phenotype
EOM = Namespace('https://elementsofmorphology.nih.gov/index.cgi?tid=')         # Elements of Morphology phentoypes
EOM_IMG = Namespace('https://elementsofmorphology.nih.gov/images/terms/')

# publication/citation/reference sources
DOI = Namespace('http://dx.doi.org/')                                         # Digital Object identifier
GENEREVIEWS = Namespace('http://www.ncbi.nlm.nih.gov/books/')                 # NCBI gene and diseases
# more bogus IRIs
ISBN = Namespace('https://monarchinitiative.org/ISBN_')                       # International Standard Book Number
ISBN_10 = Namespace('https://monarchinitiative.org/ISBN10_')                  # Same as ISBN has 10 digits pre 2007
ISBN_13 = Namespace('https://monarchinitiative.org/ISBN13_')                  # International Standard Book Number with 13 digits starts w/ 978 or 979
# 'ISBN-15': 'https://monarchinitiative.org/ISBN15_'                # I would like to think it is a typo blindly propagated   ***
J = Namespace('http://www.informatics.jax.org/reference/J:')                  # MGI-internal identifiers for pubs (Journals)
MPD = Namespace('https://phenome.jax.org/')                                   # Mouse Phenome Database
MPD_ASSAY = Namespace('https://phenome.jax.org/db/qp?rtn=views/catlines&keymeas=')  # Mouse Phenome Database assay
PMID = Namespace('http://www.ncbi.nlm.nih.gov/pubmed/')                       # PubMed Identifier
PMCID = Namespace('http://www.ncbi.nlm.nih.gov/pmc/')                         # PubMed Central Identifier
NCBIBSGENE = Namespace('http://www.ncbi.nlm.nih.gov/bookshelf/br.fcgi?book=gene&part=')         # NCBI BookShelf Gene book citation
ASPGD_REF = Namespace('http://www.aspergillusgenome.org/cgi-bin/reference/reference.pl?dbid=')  # Aspergillus DB citation

AQTLPUB = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/BT/qabstract?PUBMED_ID=')  # Animal Quantitative Trait Locus Publication
GO_REF = Namespace('http://www.geneontology.org/cgi-bin/references.cgi#GO_REF:')           # GO Reference Collection
PAINT_REF = Namespace('http://www.geneontology.org/gene-associations/submission/paint/')   # Phylogenetic Annotation INference Tool
HPO = Namespace('http://human-phenotype-ontology.org/')                                    # Human Phenotype Ontology
APO = Namespace('http://purl.obolibrary.org/obo/APO_')                                     # Ascomycete phenotype ontolog

# strains, lines, or organismal reagents
APB = Namespace('http://pb.apf.edu.au/phenbank/strain.html?id=')                          # Australian Phenome Bank
CMMR = Namespace('http://www.cmmr.ca/order.php?t=m&id=')                                  # Canadian Mouse Mutant Repository
CORIELL = Namespace('https://catalog.coriell.org/0/Sections/Search/Sample_Detail.aspx?Ref=')  # Coriell Institute for Medical Research
CORIELLCOLLECTION = Namespace('https://catalog.coriell.org/1/')
CORIELLFAMILY = Namespace('https://catalog.coriell.org/0/Sections/BrowseCatalog/FamilyTypeSubDetail.aspx?fam=')
CORIELLINDIVIDUAL = Namespace('https://catalog.coriell.org/Search?q=')
DBSNPINDIVIDUAL = Namespace('http://www.ncbi.nlm.nih.gov/SNP/snp_ind.cgi?ind_id=')     # FIXME (form only has 'sub_id')
# https://www.ncbi.nlm.nih.gov/mailman/pipermail/dbsnp-announce/2018q2/000186.html

EMMA = Namespace('https://www.infrafrontier.eu/search?keyword=EM:')                       # European Mouse Mutant Archive
JAX = Namespace('http://jaxmice.jax.org/strain/')                                         # The Jackson Laboratory
MMRRC = Namespace('https://www.mmrrc.org/catalog/sds.php?mmrrc_id=')                      # Mutant Mouse Resource & Research Centers
MPD_STRAIN = Namespace('http://phenome.jax.org/db/q?rtn=strains/details&strainid=')       # Mouse Phenome Database
MUGEN = Namespace('http://bioit.fleming.gr/mugen/Controller?workflow=ViewModel&expand_all=true&name_begins=model.block&eid=')  # Mouse Genetics
NCIMR = Namespace('https://mouse.ncifcrf.gov/available_details.asp?ID=')                  # link rot?
RBRC = Namespace('http://www2.brc.riken.jp/lab/animal/detail.php?brc_no=')                # RIKEN BioResource Research Center

# organisms and genome builds
#                                                                       # National Center for Biotechnology Information
NCBIASSEMBLY = Namespace('https://www.ncbi.nlm.nih.gov/assembly?term=')           #   Assembly  e.g. GRCh38
NCBIGENOME = Namespace('https://www.ncbi.nlm.nih.gov/genome/')                    #   Genome    e.g. 51  (for human)
# NCBITAXON = Namespace('http://purl.obolibrary.org/obo/NCBITaxon_')                #   Taxon     e.g. 9606
NCBITAXON = Namespace('http://purl.obolibrary.org/obo/NCBITaxon_')                #   Taxon     e.g. 9606
OMIA_BREED = Namespace('https://monarchinitiative.org/model/OMIA-breed:')         # Local IRI for Online Inheritance In Animal breeds
UCSC = Namespace('ftp://hgdownload.cse.ucsc.edu/goldenPath/')                     # University of California, Santa Cruz golden path
UCSCBUILD = Namespace('http://genome.ucsc.edu/cgi-bin/hgGateway?db=')             # University of California, Santa Cruz genome build
# homology
HOMOLOGENE = Namespace('http://www.ncbi.nlm.nih.gov/homologene/')                 # Putative Homology Groups
KEGG_KO = Namespace('http://www.kegg.jp/dbget-bin/www_bget?ko:')                  # Kyoto Encyclopedia of Genes and Genomes (KEGG Orthology)
PANTHER = Namespace('http://www.pantherdb.org/panther/family.do?clsAccession=')   # Protein ANalysis THrough Evolutionary Relationships

# variants / traits

# 'AnimalQTLdb': 'previously'
HORSEQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/EC/qdetails?QTL_ID=')
CATTLEQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/BT/qdetails?QTL_ID=')
CATFISHQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/IP/qdetails?QTL_ID=')
CHICKENQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/GG/qdetails?QTL_ID=')
PIGQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/SS/qdetails?QTL_ID=')
RAINBOW_TROUTQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/OM/qdetails?QTL_ID=')
SHEEPQTL = Namespace('https://www.animalgenome.org/cgi-bin/QTLdb/OA/qdetails?QTL_ID=')

BGD = Namespace('http://bovinegenome.org/genepages/btau40/genes/')                # The Bovine Genome Database (no direct link)
#                                                                       # 'http://128.206.116.13:8080/bovinemine/report.do?id='

CLINVAR = Namespace('http://www.ncbi.nlm.nih.gov/clinvar/')                       # Clinical Variation in Human
CLINVARVARIANT = Namespace('http://www.ncbi.nlm.nih.gov/clinvar/variation/')      # ClinVar cooked variants
CLINVARSUBMITTERS = Namespace('http://www.ncbi.nlm.nih.gov/clinvar/submitters/')  # ClinVar raw variants
COSMIC = Namespace('http://cancer.sanger.ac.uk/cosmic/mutation/overview?id=')     # Catalogue Of Somatic Mutations In Cancer
HGMD = Namespace('http://www.hgmd.cf.ac.uk/ac/gene.php?gene=')                    # Human Gene Mutation Database
DBSNP = Namespace('http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=')     # Small Variation
DBVAR = Namespace('http://www.ncbi.nlm.nih.gov/dbvar/')                           # Large Variation
GWAS = Namespace('https://www.ebi.ac.uk/gwas/variants/')                          # Genome Wide Association Study Catalog

# pathways
KEGG_PATH = Namespace('http://www.kegg.jp/dbget-bin/www_bget?path:')              # Kyoto Encyclopedia of Genes and Genomes (pathways)
KEGG_IMG = Namespace('http://www.genome.jp/kegg/pathway/map/')                    # Pathway Visualization
REACT = Namespace('http://www.reactome.org/PathwayBrowser/#/')                    # Manually curated pathway database
SMPDB = Namespace('http://smpdb.ca/view/')                                        # Small Molecule Pathway Database

# genes (and RNAs and transcripts)
ASPGD = Namespace('http://www.aspergillusgenome.org/cgi-bin/locus.pl?dbid=')              # Aspergillus Genome Database
BIOGRID = Namespace('http://thebiogrid.org/')                                             # Biological General Repository for Interaction Datasets
CCDS = Namespace('http://www.ncbi.nlm.nih.gov/CCDS/CcdsBrowse.cgi?REQUEST=CCDS&DATA=')    # Consensus CDS (CoDing Sequence)
CGNC = Namespace('http://birdgenenames.org/cgnc/GeneReport?id=')                          # Chicken Gene Nomenclature Consortium
DICTYBASE = Namespace('http://dictybase.org/gene/')                                       # Dictyostelium discoideum database (social amoebae)
ECOGENE = Namespace('http://ecogene.org/gene/')                                           # Escherichia coli K-1
ENSEMBL = Namespace('http://ensembl.org/id/')                                             # joint EMBL, EBI, Sanger Institute central resource
ENSEMBLGENOME = Namespace('http://www.ensemblgenomes.org/id/')                            # The Ensembl genome annotation system
FLYBASE = Namespace('http://flybase.org/reports/')                                        # Fruitfly database
GENATLAS = Namespace('http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol=')         # gene mapping and genetic diseases (Human)
GENBANK = Namespace('http://www.ncbi.nlm.nih.gov/nuccore/')                               # NCBI nucleotide sequences
# HGNC = Namespace('http://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=')        # pre drupal site
# HGNC = Namespace('https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:')    # HUGO Gene Nomenclature Committee (Human)
HGNC = Namespace('https://identifiers.org/hgnc/')    # HUGO Gene Nomenclature Committee (Human)
HGNC_symbol = Namespace('https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/')    # HUGO Gene Nomenclature Committee (Human)
IMPC = Namespace('https://www.mousephenotype.org/data/genes/')                             # International Mouse Phenotyping Consortium (MGI:nnn)
IMPC_PIPE = Namespace('https://www.mousephenotype.org/impress/PipelineInfo?id=')         # <pipeline-key>
IMPC_PROC = Namespace('https://www.mousephenotype.org/impress/ProcedureInfo?action=list&procID=')  # <procedure-key>[&pipeID=<pipeline-key>]
IMPC_PARAM = Namespace('https://www.mousephenotype.org/impress/OntologyInfo?action=list&procID=')  # <procedure-key>#<prarameter-key>
KEGG_HSA = Namespace('http://www.kegg.jp/dbget-bin/www_bget?hsa:')                        # Kyoto Encyclopedia of Genes and Genomes (Human)
MGI = Namespace('http://www.informatics.jax.org/accession/MGI:')                          # Mouse Genome Informatics
MIRBASE = Namespace('http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=')                 # microRNA nomenclature, sequences & annotation
NCBIGENE = Namespace('https://www.ncbi.nlm.nih.gov/gene/')                                # National Center for Biotechnology Information (Genes)
POMBASE = Namespace('https://www.pombase.org/spombe/result/')                             # Database for fission yeast Schizosaccharomyces pombe  ***
REFSEQ = Namespace('http://www.ncbi.nlm.nih.gov/refseq/?term=')                           # NCBI Reference Sequence Database
RGD = Namespace('http://rgd.mcw.edu/rgdweb/report/gene/main.html?id=')                    # Rat Genome Database
RGDREF = Namespace('http://rgd.mcw.edu/rgdweb/report/reference/main.html?id=')            # Rat Genome Database Reference publications
SGD = Namespace('https://www.yeastgenome.org/locus/')                                     # Saccharomyces Genome Database
SGD_REF = Namespace('https://www.yeastgenome.org/reference/')                             # Saccharomyces Genome Database Reference publications
TAIR = Namespace('https://www.arabidopsis.org/servlets/TairObject?type=locus&id=')        # The Arabidopsis Information Resource
VGNC = Namespace('https://vertebrate.genenames.org/data/gene-symbol-report/#!/vgnc_id/')  # Vertebrate Gene Nomenclature Committee
WORMBASE = Namespace('https://www.wormbase.org/get?name=')                                # Caenorhabditis elegans Database (nematodes) ie WBGene00000001
XENBASE = Namespace('http://www.xenbase.org/gene/showgene.do?method=display&geneId=')     # Xenopus Database (frog)
ZFIN = Namespace('http://zfin.org/')                                                      # Zebrafish Information Network

# proteins (and protein/macromolecular complexes)
COMPLEXPORTAL = Namespace('https://www.ebi.ac.uk/complexportal/complex/')                 # Manually curated, encyclopaedic resource of macromolecular complexes
EC = Namespace('https://www.enzyme-database.org/query.php?ec=')                           # Enzyme Commission (nomenclature)
HPRD = Namespace('http://www.hprd.org/protein/')                                          # Human Protein Reference Database
NCBIPROTEIN = Namespace('http://www.ncbi.nlm.nih.gov/protein/')                           # NCBI amino acid sequences
PDB = Namespace('http://www.ebi.ac.uk/pdbsum/')                                           # Protein Data Bank

SWISSPROT = Namespace('http://identifiers.org/SwissProt:')                                # UniProt Knowledgebase UniProtKB  Manual
TREMBL = Namespace('http://purl.uniprot.org/uniprot/')                                    # UniProt Knowledgebase UniProtKB  Automated
UNIPROTKB = Namespace('http://identifiers.org/uniprot/')                                  # UniProt Knowledgebase UniProtKB  Both

INTERPRO = Namespace('https://www.ebi.ac.uk/interpro/entry/InterPro/')                    # Classification of protein families
#                                                                                   # may become "GtoPdb"
IUPHAR = Namespace('http://www.guidetopharmacology.org/GRAC/ObjectDisplayForward?objectId=')  # Omnibus pharmacological information portal

# Drugs, chemicals, compounds
CID = Namespace('http://pubchem.ncbi.nlm.nih.gov/compound/')          # NCBI PubChem Compound
DRUGBANK = Namespace('http://www.drugbank.ca/drugs/')                 # DrugBank database (drugs and drug targets)
OAE = Namespace('http://purl.obolibrary.org/obo/OAE_')                # Ontology of Adverse Events
RXCUI = Namespace('http://purl.bioontology.org/ontology/RXNORM/')     # Normalized names for clinical drugs (from Unified Medical Language System)
MEDDRA = Namespace('http://purl.bioontology.org/ontology/MEDDRA/')    # Medical Dictionary for Regulatory Activities
FDADRUG = Namespace('http://www.fda.gov/Drugs/InformationOnDrugs/')   # U.S. Food & Drug Administration Drug  (*** what uses? seems useless)
BT = Namespace('http://c.biothings.io/#')                             # MyChem (BioThings)
UNII = Namespace('http://fdasis.nlm.nih.gov/srs/unii/')               # Unique Ingredient Identifier (from FDA Substance Registration System)
GINAS = Namespace('http://tripod.nih.gov/ginas/app/substance#')       # Global Ingredient Archival System (National Institute of Health)
HMDB = Namespace('http://www.hmdb.ca/metabolites/')                   # Human Metabolome Database
WD_PROP = Namespace('https://www.wikidata.org/wiki/Property:')        # Wikidata Property
WD_ENTITY = Namespace('https://www.wikidata.org/wiki/')               # Wikidata

PMID = Namespace('http://www.ncbi.nlm.nih.gov/pubmed/')
ORPHANET = Namespace('http://www.orpha.net/ORDO/Orphanet_')
UMLS = Namespace('http://linkedlifedata.com/resource/umls/id/')
oboInOwl = Namespace('http://www.geneontology.org/formats/oboInOwl#')

MONDONS = Namespace('http://purl.obolibrary.org/obo/mondo#')
# # Monarch-specific
# '': 'https://monarchinitiative.org/'                                # local BASE IRI
# 'MONARCH': 'https://monarchinitiative.org/MONARCH_'                 # local BOGUS IRI effectivly bnodes but less
# 'BNODE': 'https://monarchinitiative.org/.well-known/genid/'         # local RDF Skolemized Blank Node
#
# 'MonarchData': 'https://data.monarchinitiative.org/ttl/'            # Bleeding edge RDF data
# 'MonarchArchive': 'https://archive.monarchinitiative.org/'          # Release RDF data
# 'MonarchLogoRepo': 'https://github.com/monarch-initiative/monarch-ui/blob/master/public/img/sources/'    # Monarch's stash of logos for sources we ingest - this is used to set schemalogo in Dataset.py
#
# 'biolink': 'https://w3id.org/biolink/vocab/'                         # Biolink model
#
# # other semantic-web items
# 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'                # Resource Description Framework
# 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'                     # Resource Description Framework Schema
# 'dc': 'http://purl.org/dc/terms/'                                   # Dublin Core (metadata) (terms is superset of elements)
# 'foaf': 'http://xmlns.com/foaf/0.1/'                                # Friend Of A Friend (social)
# 'xml': 'http://www.w3.org/XML/1998/namespace'                       # Extensible Markup Language
# 'xsd': 'http://www.w3.org/2001/XMLSchema#'                          # XML Schema Definition
# 'owl': 'http://www.w3.org/2002/07/owl#'                             # Web Ontology Language
# 'skos': 'http://www.w3.org/2004/02/skos/core#'                      # Simple Knowledge Organization System
# # 'Annotation': 'http://www.w3.org/ns/oa#Annotation'                # Web annotation
# 'schema': 'http://schema.org/'                                      # Schema.org "provides schemas for structured data on the Internet"
#
# # dataset description
# 'dcat': 'http://www.w3.org/ns/dcat#'                                # Data Catalog Vocabulary
# 'dctypes': 'http://purl.org/dc/dcmitype/'                           # Dublin Core Metadata Initiative (types)
# 'pav': 'http://purl.org/pav/'                                       # Provenance, Authoring and Versioning
# 'cito': 'http://purl.org/spar/cito/'                                # Citation Typing Ontology
# 'void': 'http://rdfs.org/ns/void#'                                  # Vocabulary of Interlinked Datasets (VOID)
#
# # ontologies
# 'AQTLTrait': 'http://identifiers.org/animalqtltrait/'               # Animal Quantitative Trait Loci Database
# # FIXME - should get integrated into Upheno
#
# 'BFO': 'http://purl.obolibrary.org/obo/BFO_'                        # Basic Formal Ontology
# 'COHD': 'http://purl.obolibrary.org/obo/COHD_'                      # Columbia Open Health Data
# 'CHEBI': 'http://purl.obolibrary.org/obo/CHEBI_'                    # Chemicals of Biological Interest
# 'CHR': 'http://purl.obolibrary.org/obo/CHR_'                        # Chromosome Ontology
# 'CL': 'http://purl.obolibrary.org/obo/CL_'                          # Cell Ontology (cell types)
# 'CLO': 'http://purl.obolibrary.org/obo/CLO_'                        # Cell Line Ontology
# 'CMO': 'http://purl.obolibrary.org/obo/CMO_'                        # Clinical Measurements Ontology
# 'EDAM-DATA': 'http://edamontology.org/data_'                        # Data and Methods Ontology (data artifacts)
# 'DC_CL': 'http://purl.obolibrary.org/obo/DC_CL'                     #  *** seeing it fixed in github but not yet live was `DC`
# 'DECIPHER': 'https://decipher.sanger.ac.uk/syndrome/'               # Deciphering Developmental Disease
# 'DOID': 'http://purl.obolibrary.org/obo/DOID_'                      # Human Disease Ontology
# 'ECO': 'http://purl.obolibrary.org/obo/ECO_'                        # Evidence Code Ontology
# 'EFO': 'http://www.ebi.ac.uk/efo/EFO_'                              # Experimental Factor Ontology (all kinds of stuff)
# 'ENVO': 'http://purl.obolibrary.org/obo/ENVO_'                      # Environment Ontology
# 'ERO': 'http://purl.obolibrary.org/obo/ERO_'                        # Eeagle-i Resource Ontology
# 'faldo': 'http://biohackathon.org/resource/faldo#'                  # Feature Annotation Location Description Ontology
# 'FBcv': 'http://purl.obolibrary.org/obo/FBcv_'                      # FlyBase Controled Vocabulary (includes phenotypes)
# 'FBbt': 'http://purl.obolibrary.org/obo/FBbt_'                      # FlyBase anatomy
# 'FBdv': 'http://purl.obolibrary.org/obo/FBdv_'                      # Flybase developmental stages
# # till we get a purl? `FBgn': 'http://flybase.org/reports/'         # flybase gene?
# 'GARD': 'http://purl.obolibrary.org/obo/GARD_'                      # Genetic and Rare Diseases (GARD) Information Center
# 'GENO': 'http://purl.obolibrary.org/obo/GENO_'                      # Genotype Partonomy Ontology
# 'GO': 'http://purl.obolibrary.org/obo/GO_'                          # Gene Ontology
# 'HP': 'http://purl.obolibrary.org/obo/HP_'                          # Human Phenotype Ontology
# 'IAO': 'http://purl.obolibrary.org/obo/IAO_'                        # Information Artifact Ontology
# 'ICD9': 'http://purl.obolibrary.org/obo/ICD9_'                      # International Classification of Disease 9th Rev
# 'KEGG-ds': 'http://purl.obolibrary.org/KEGG-ds_'                    # Kyoto Encyclopedia of Genes and Genomes Disease Ontology
# 'LPT': 'http://purl.obolibrary.org/obo/LPT_'                        # Livestock Phenotypic Trait Ontology
# 'MA': 'http://purl.obolibrary.org/obo/MA_'                          # Mouse Anatomy Ontology
# 'MedGen': 'http://www.ncbi.nlm.nih.gov/medgen/'                     # Human Medical Genetics vocabulary
# 'MESH': 'http://id.nlm.nih.gov/mesh/'                               # Medical Subject Headings (medical diseases, phenotypes, and drugs)
# 'MP': 'http://purl.obolibrary.org/obo/MP_'                          # Mammalian Phenotype Ontology
# 'MPATH': 'http://purl.obolibrary.org/obo/MPATH_'                    # Mammalian Pathology Ontology
# 'NBO': 'http://purl.obolibrary.org/obo/NBO_'                        # NeuroBehavior Ontology
# 'OBA': 'http://purl.obolibrary.org/obo/OBA_'                        # Ontology of Biological Attributes (traits)
# 'OBAN': 'http://purl.org/oban/'                                     # Open Biomedical Annotation Model
# 'OBI': 'http://purl.obolibrary.org/obo/OBI_'                        # Ontology of Biomedical Investigations
# 'OBO': 'http://purl.obolibrary.org/obo/'                            # Biological Ontology namespace (this is not itself an ontology)
# 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#'         # obo-specific annotation properties, like synonym types
# # 'OMIA' was http://omia.angis.org.au/ IS https://omia.org/         # (see about helping to update original data)
# 'OMIA': 'https://omia.org/OMIA'                                     # Online Mendelian Inheritance in Animals (disease/species)
# # LIDIA seems retired. so these are not resovable                   # Also: http://www.vetsci.usyd.edu.au/lida/
# 'LIDA': 'http://sydney.edu.au/vetscience/lida/dogs/search/disorder/'  # Listing of Inherited Disorders in Animals (defunct?)
# 'OMIM': 'http://omim.org/entry/'                                    # Online Mendelian Inheritance in Man (human disease and variants)
# 'OMIMPS': 'https://www.omim.org/phenotypicSeries/PS'                   # Online Mendelian Inheritance in Man (phenotypes)
# 'ORPHA': 'http://www.orpha.net/ORDO/Orphanet_'                      # Rare diseases and Orphan drugs
# 'PATO': 'http://purl.obolibrary.org/obo/PATO_'                      # Phenotypic Quality Ontology
# 'PCO': 'http://purl.obolibrary.org/obo/PCO_'                        # Population and Community Ontology
# 'PR': 'http://purl.obolibrary.org/obo/PR_'                          # Protein ontology
# 'PW': 'http://purl.obolibrary.org/obo/PW_'                          # PathWay ontology
# 'RO': 'http://purl.obolibrary.org/obo/RO_'                          # Relationship Ontology
# 'SCTID': 'http://purl.obolibrary.org/obo/SCTID_'                    # SNOMED
# 'SIO': 'http://semanticscience.org/resource/SIO_'                   # SemanticScience Integrated Ontology (information artifacts)
# 'SNOMED': 'http://purl.obolibrary.org/obo/SNOMED_'                  # Diseases and Phenotypes
# 'SO': 'http://purl.obolibrary.org/obo/SO_'                          # Sequence Ontology
# 'STATO': 'http://purl.obolibrary.org/obo/STATO_'                    # Statistics Ontology
# 'UBERON': 'http://purl.obolibrary.org/obo/UBERON_'                  # Integrated anatomy ontology (metazoans, mostly)
# 'UPHENO': 'http://purl.obolibrary.org/obo/UPHENO_'                  # Integrated phenotype ontology, and normal traits
# 'UMLS': 'http://linkedlifedata.com/resource/umls/id/'               # Unified Medical Language system
# 'UO': 'http://purl.obolibrary.org/obo/UO_'                          # Units of measurements
# 'VT': 'http://purl.obolibrary.org/obo/VT_'                          # Vertebrate Trait Ontology
# 'WBPhenotype': 'http://purl.obolibrary.org/obo/WBPhenotype_'        # WormBase Phenotypes (nematode)
# 'XCO': 'http://purl.obolibrary.org/obo/XCO_'                        # Experimental Conditions Ontology
# 'ZFA': 'http://purl.obolibrary.org/obo/ZFA_'                        # Zebrafish Anatomy Ontology
# 'ZFS': 'http://purl.obolibrary.org/obo/ZFS_'                        # Zebrafish Staging
# 'ZP': 'http://purl.obolibrary.org/obo/ZP_'                          # Zebrafish Phenotype Ontology
# 'WBbt': 'http://purl.obolibrary.org/obo/WBbt_'                      # C. elegans gross anatomy
# 'EMAPA': 'http://purl.obolibrary.org/obo/EMAPA_'                    # Mouse gross anatomy and development, timed
# 'XAO': 'http://purl.obolibrary.org/obo/XAO_'                        # Xenopus Anatomy and development
# 'MONDO': 'http://purl.obolibrary.org/obo/MONDO_'                    # Monarch Disease Ontology
# 'NCIT': 'http://purl.obolibrary.org/obo/NCIT_'                      # National Cancer Institute Thesaurus
# 'SEPIO': 'http://purl.obolibrary.org/obo/SEPIO_'                    # Scientific Evidence and Provenance Information Ontology
# 'VIVO': 'http://vivoweb.org/ontology/core#'                         # ontology for representing scholarship
# 'vfb': 'http://virtualflybrain.org/reports/'                        # Drosophila neuroanatomy
#
# # phenotype
# 'EOM': 'https://elementsofmorphology.nih.gov/index.cgi?tid='         # Elements of Morphology phentoypes
# 'EOM_IMG': 'https://elementsofmorphology.nih.gov/images/terms/'
#
# # publication/citation/reference sources
# 'DOI': 'http://dx.doi.org/'                                         # Digital Object identifier
# 'GeneReviews': 'http://www.ncbi.nlm.nih.gov/books/'                 # NCBI gene and diseases
# # more bogus IRIs
# 'ISBN': 'https://monarchinitiative.org/ISBN_'                       # International Standard Book Number
# 'ISBN-10': 'https://monarchinitiative.org/ISBN10_'                  # Same as ISBN has 10 digits pre 2007
# 'ISBN-13': 'https://monarchinitiative.org/ISBN13_'                  # International Standard Book Number with 13 digits starts w/ 978 or 979
# # 'ISBN-15': 'https://monarchinitiative.org/ISBN15_'                # I would like to think it is a typo blindly propagated   ***
# 'J': 'http://www.informatics.jax.org/reference/J:'                  # MGI-internal identifiers for pubs (Journals)
# 'MPD': 'https://phenome.jax.org/'                                   # Mouse Phenome Database
# 'MPD-assay': 'https://phenome.jax.org/db/qp?rtn=views/catlines&keymeas='  # Mouse Phenome Database assay
# 'PMID': 'http://www.ncbi.nlm.nih.gov/pubmed/'                       # PubMed Identifier
# 'PMCID': 'http://www.ncbi.nlm.nih.gov/pmc/'                         # PubMed Central Identifier
# 'NCBIBSgene': 'http://www.ncbi.nlm.nih.gov/bookshelf/br.fcgi?book=gene&part='         # NCBI BookShelf Gene book citation
# 'AspGD_REF': 'http://www.aspergillusgenome.org/cgi-bin/reference/reference.pl?dbid='  # Aspergillus DB citation
#
# 'AQTLPub': 'https://www.animalgenome.org/cgi-bin/QTLdb/BT/qabstract?PUBMED_ID='  # Animal Quantitative Trait Locus Publication
# 'GO_REF': 'http://www.geneontology.org/cgi-bin/references.cgi#GO_REF:'           # GO Reference Collection
# 'PAINT_REF': 'http://www.geneontology.org/gene-associations/submission/paint/'   # Phylogenetic Annotation INference Tool
# 'HPO': 'http://human-phenotype-ontology.org/'                                    # Human Phenotype Ontology
# 'APO': 'http://purl.obolibrary.org/obo/APO_'                                     # Ascomycete phenotype ontolog
#
# # strains, lines, or organismal reagents
# 'APB': 'http://pb.apf.edu.au/phenbank/strain.html?id='                          # Australian Phenome Bank
# 'CMMR': 'http://www.cmmr.ca/order.php?t=m&id='                                  # Canadian Mouse Mutant Repository
# 'Coriell': 'https://catalog.coriell.org/0/Sections/Search/Sample_Detail.aspx?Ref='  # Coriell Institute for Medical Research
# 'CoriellCollection': 'https://catalog.coriell.org/1/'
# 'CoriellFamily': 'https://catalog.coriell.org/0/Sections/BrowseCatalog/FamilyTypeSubDetail.aspx?fam='
# 'CoriellIndividual': 'https://catalog.coriell.org/Search?q='
# 'dbSNPIndividual': 'http://www.ncbi.nlm.nih.gov/SNP/snp_ind.cgi?ind_id='      # FIXME (form only has 'sub_id')
# # https://www.ncbi.nlm.nih.gov/mailman/pipermail/dbsnp-announce/2018q2/000186.html
#
# 'EMMA': 'https://www.infrafrontier.eu/search?keyword=EM:'                       # European Mouse Mutant Archive
# 'JAX': 'http://jaxmice.jax.org/strain/'                                         # The Jackson Laboratory
# 'MMRRC': 'https://www.mmrrc.org/catalog/sds.php?mmrrc_id='                      # Mutant Mouse Resource & Research Centers
# 'MPD-strain': 'http://phenome.jax.org/db/q?rtn=strains/details&strainid='       # Mouse Phenome Database
# 'MUGEN': 'http://bioit.fleming.gr/mugen/Controller?workflow=ViewModel&expand_all=true&name_begins=model.block&eid='  # Mouse Genetics
# 'NCIMR': 'https://mouse.ncifcrf.gov/available_details.asp?ID='                  # link rot?
# 'RBRC': 'http://www2.brc.riken.jp/lab/animal/detail.php?brc_no='                # RIKEN BioResource Research Center
#
# # organisms and genome builds
# #                                                                       # National Center for Biotechnology Information
# 'NCBIAssembly': 'https://www.ncbi.nlm.nih.gov/assembly?term='           #   Assembly  e.g. GRCh38
# 'NCBIGenome': 'https://www.ncbi.nlm.nih.gov/genome/'                    #   Genome    e.g. 51  (for human)
# 'NCBITaxon': 'http://purl.obolibrary.org/obo/NCBITaxon_'                #   Taxon     e.g. 9606
# 'OMIA-breed': 'https://monarchinitiative.org/model/OMIA-breed:'         # Local IRI for Online Inheritance In Animal breeds
# 'UCSC': 'ftp://hgdownload.cse.ucsc.edu/goldenPath/'                     # University of California, Santa Cruz golden path
# 'UCSCBuild': 'http://genome.ucsc.edu/cgi-bin/hgGateway?db='             # University of California, Santa Cruz genome build
# # homology
# 'HOMOLOGENE': 'http://www.ncbi.nlm.nih.gov/homologene/'                 # Putative Homology Groups
# 'KEGG-ko': 'http://www.kegg.jp/dbget-bin/www_bget?ko:'                  # Kyoto Encyclopedia of Genes and Genomes (KEGG Orthology)
# 'PANTHER': 'http://www.pantherdb.org/panther/family.do?clsAccession='   # Protein ANalysis THrough Evolutionary Relationships
#
# # variants / traits
#
# # 'AnimalQTLdb': 'previously'
# 'horseQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/EC/qdetails?QTL_ID='
# 'cattleQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/BT/qdetails?QTL_ID='
# 'catfishQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/IP/qdetails?QTL_ID='
# 'chickenQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/GG/qdetails?QTL_ID='
# 'pigQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/SS/qdetails?QTL_ID='
# 'rainbow_troutQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/OM/qdetails?QTL_ID='
# 'sheepQTL': 'https://www.animalgenome.org/cgi-bin/QTLdb/OA/qdetails?QTL_ID='
#
# 'BGD': 'http://bovinegenome.org/genepages/btau40/genes/'                # The Bovine Genome Database (no direct link)
# #                                                                       # 'http://128.206.116.13:8080/bovinemine/report.do?id='
#
# 'ClinVar': 'http://www.ncbi.nlm.nih.gov/clinvar/'                       # Clinical Variation in Human
# 'ClinVarVariant': 'http://www.ncbi.nlm.nih.gov/clinvar/variation/'      # ClinVar cooked variants
# 'ClinVarSubmitters': 'http://www.ncbi.nlm.nih.gov/clinvar/submitters/'  # ClinVar raw variants
# 'COSMIC': 'http://cancer.sanger.ac.uk/cosmic/mutation/overview?id='     # Catalogue Of Somatic Mutations In Cancer
# 'HGMD': 'http://www.hgmd.cf.ac.uk/ac/gene.php?gene='                    # Human Gene Mutation Database
# 'dbSNP': 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs='     # Small Variation
# 'dbVar': 'http://www.ncbi.nlm.nih.gov/dbvar/'                           # Large Variation
# 'GWAS': 'https://www.ebi.ac.uk/gwas/variants/'                          # Genome Wide Association Study Catalog
#
# # pathways
# 'KEGG-path': 'http://www.kegg.jp/dbget-bin/www_bget?path:'              # Kyoto Encyclopedia of Genes and Genomes (pathways)
# 'KEGG-img': 'http://www.genome.jp/kegg/pathway/map/'                    # Pathway Visualization
# 'REACT': 'http://www.reactome.org/PathwayBrowser/#/'                    # Manually curated pathway database
# 'SMPDB': 'http://smpdb.ca/view/'                                        # Small Molecule Pathway Database
#
# # genes (and RNAs and transcripts)
# 'AspGD': 'http://www.aspergillusgenome.org/cgi-bin/locus.pl?dbid='              # Aspergillus Genome Database
# 'BIOGRID': 'http://thebiogrid.org/'                                             # Biological General Repository for Interaction Datasets
# 'CCDS': 'http://www.ncbi.nlm.nih.gov/CCDS/CcdsBrowse.cgi?REQUEST=CCDS&DATA='    # Consensus CDS (CoDing Sequence)
# 'CGNC': 'http://birdgenenames.org/cgnc/GeneReport?id='                          # Chicken Gene Nomenclature Consortium
# 'dictyBase': 'http://dictybase.org/gene/'                                       # Dictyostelium discoideum database (social amoebae)
# 'EcoGene': 'http://ecogene.org/gene/'                                           # Escherichia coli K-1
# 'ENSEMBL': 'http://ensembl.org/id/'                                             # joint EMBL, EBI, Sanger Institute central resource
# 'EnsemblGenome': 'http://www.ensemblgenomes.org/id/'                            # The Ensembl genome annotation system
# 'FlyBase': 'http://flybase.org/reports/'                                        # Fruitfly database
# 'Genatlas': 'http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol='         # gene mapping and genetic diseases (Human)
# 'GenBank': 'http://www.ncbi.nlm.nih.gov/nuccore/'                               # NCBI nucleotide sequences
# # 'HGNC': 'http://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id='        # *** pre drupal site
# 'HGNC': 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:'    # HUGO Gene Nomenclature Committee (Human)
# 'IMPC': 'https://www.mousephenotype.org/data/genes/'                             # International Mouse Phenotyping Consortium (MGI:nnn)
# 'IMPC-pipe': 'https://www.mousephenotype.org/impress/PipelineInfo?id='         # <pipeline-key>
# 'IMPC-proc': 'https://www.mousephenotype.org/impress/ProcedureInfo?action=list&procID='  # <procedure-key>[&pipeID=<pipeline-key>]
# 'IMPC-param': 'https://www.mousephenotype.org/impress/OntologyInfo?action=list&procID='  # <procedure-key>#<prarameter-key>
# 'KEGG-hsa': 'http://www.kegg.jp/dbget-bin/www_bget?hsa:'                        # Kyoto Encyclopedia of Genes and Genomes (Human)
# 'MGI': 'http://www.informatics.jax.org/accession/MGI:'                          # Mouse Genome Informatics
# 'miRBase': 'http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc='                 # microRNA nomenclature, sequences & annotation
# 'NCBIGene': 'https://www.ncbi.nlm.nih.gov/gene/'                                # National Center for Biotechnology Information (Genes)
# 'PomBase': 'https://www.pombase.org/spombe/result/'                             # Database for fission yeast Schizosaccharomyces pombe  ***
# 'RefSeq': 'http://www.ncbi.nlm.nih.gov/refseq/?term='                           # NCBI Reference Sequence Database
# 'RGD': 'http://rgd.mcw.edu/rgdweb/report/gene/main.html?id='                    # Rat Genome Database
# 'RGDRef': 'http://rgd.mcw.edu/rgdweb/report/reference/main.html?id='            # Rat Genome Database Reference publications
# 'SGD': 'https://www.yeastgenome.org/locus/'                                     # Saccharomyces Genome Database
# 'SGD_REF': 'https://www.yeastgenome.org/reference/'                             # Saccharomyces Genome Database Reference publications
# 'TAIR': 'https://www.arabidopsis.org/servlets/TairObject?type=locus&id='        # The Arabidopsis Information Resource
# 'VGNC': 'https://vertebrate.genenames.org/data/gene-symbol-report/#!/vgnc_id/'  # Vertebrate Gene Nomenclature Committee
# 'WormBase': 'https://www.wormbase.org/get?name='                                # Caenorhabditis elegans Database (nematodes) ie WBGene00000001
# 'Xenbase': 'http://www.xenbase.org/gene/showgene.do?method=display&geneId='     # Xenopus Database (frog)
# 'ZFIN': 'http://zfin.org/'                                                      # Zebrafish Information Network
#
# # proteins (and protein/macromolecular complexes)
# 'ComplexPortal': 'https://www.ebi.ac.uk/complexportal/complex/'                 # Manually curated, encyclopaedic resource of macromolecular complexes
# 'EC': 'https://www.enzyme-database.org/query.php?ec='                           # Enzyme Commission (nomenclature)
# 'HPRD': 'http://www.hprd.org/protein/'                                          # Human Protein Reference Database
# 'NCBIProtein': 'http://www.ncbi.nlm.nih.gov/protein/'                           # NCBI amino acid sequences
# 'PDB': 'http://www.ebi.ac.uk/pdbsum/'                                           # Protein Data Bank
#
# 'SwissProt': 'http://identifiers.org/SwissProt:'                                # UniProt Knowledgebase UniProtKB  Manual
# 'TrEMBL': 'http://purl.uniprot.org/uniprot/'                                    # UniProt Knowledgebase UniProtKB  Automated
# 'UniProtKB': 'http://identifiers.org/uniprot/'                                  # UniProt Knowledgebase UniProtKB  Both
#
# 'InterPro': 'https://www.ebi.ac.uk/interpro/entry/InterPro/'                    # Classification of protein families
# #                                                                                   # may become "GtoPdb"
# 'IUPHAR': 'http://www.guidetopharmacology.org/GRAC/ObjectDisplayForward?objectId='  # Omnibus pharmacological information portal
#
# # Drugs, chemicals, compounds
# 'CID': 'http://pubchem.ncbi.nlm.nih.gov/compound/'          # NCBI PubChem Compound
# 'DrugBank': 'http://www.drugbank.ca/drugs/'                 # DrugBank database (drugs and drug targets)
# 'OAE': 'http://purl.obolibrary.org/obo/OAE_'                # Ontology of Adverse Events
# 'RXCUI': 'http://purl.bioontology.org/ontology/RXNORM/'     # Normalized names for clinical drugs (from Unified Medical Language System)
# 'MEDDRA': 'http://purl.bioontology.org/ontology/MEDDRA/'    # Medical Dictionary for Regulatory Activities
# 'FDADrug': 'http://www.fda.gov/Drugs/InformationOnDrugs/'   # U.S. Food & Drug Administration Drug  (*** what uses? seems useless)
# 'BT': 'http://c.biothings.io/#'                             # MyChem (BioThings)
# 'UNII': 'http://fdasis.nlm.nih.gov/srs/unii/'               # Unique Ingredient Identifier (from FDA Substance Registration System)
# 'GINAS': 'http://tripod.nih.gov/ginas/app/substance#'       # Global Ingredient Archival System (National Institute of Health)
# 'HMDB': 'http://www.hmdb.ca/metabolites/'                   # Human Metabolome Database
# 'WD_Prop': 'https://www.wikidata.org/wiki/Property:'        # Wikidata Property
# 'WD_Entity': 'https://www.wikidata.org/wiki/'               # Wikidata
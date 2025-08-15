"""Generate gene-phenotype associations TSV file

This module creates a TSV file with gene-phenotype associations extracted from OMIM morbidmap data.
Output format: two columns with MIM IDs for genes and phenotypes.
"""

import csv
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from pathlib import Path

# Import from omim2obo.config for paths, but handle import errors gracefully
try:
    from omim2obo.config import ROOT_DIR, DATA_DIR
except ImportError:
    # Fallback if dependencies are missing
    ROOT_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT_DIR / 'data'

# Import parser functions, with fallback implementations if dependencies are missing
try:
    from omim2obo.parsers.omim_txt_parser import parse_morbid_map, get_phenotype_genes, read_mim_file_as_lines
    USING_OMIM_PARSERS = True
except ImportError:
    USING_OMIM_PARSERS = False
    print("Warning: Could not import omim2obo parsers, using fallback implementations", file=sys.stderr)

# Fallback implementations for when dependencies are missing
if not USING_OMIM_PARSERS:
    # Constants from omim_txt_parser
    MORBIDMAP_PHENOTYPE_MAPPING_KEY_MEANINGS = {
        '1': 'The disorder is placed on the map based on its association with a gene, but the underlying defect is not known.',
        '2': 'The disorder has been placed on the map by linkage or other statistical method; no mutation has been found.',
        '3': 'The molecular basis for the disorder is known; a mutation has been found in the gene.',
        '4': 'A contiguous gene deletion or duplication syndrome, multiple genes are deleted or duplicated causing the phenotype.',
    }

    def read_mim_file_as_lines(path) -> List[str]:
        """Read MIM file as list of field values, rather than a dataframe."""
        with open(path, 'r') as fin:
            lines: List[str] = fin.readlines()
            # Remove # comments
            lines = [x for x in lines if not x.startswith('#')]
            return lines

    def parse_morbid_map(lines) -> Dict[str, Dict]:
        """Parse morbid map file."""
        phenotype_label_regex = re.compile(r'(.*)(\d{6})\s*(?:\((\d+)\))?')
        phenotype_label_no_mim_regex = re.compile(r'(.*)\s+\((\d+)\)')

        gene_phenotypes: Dict[str, Dict] = {}
        for line in lines:
            if line.startswith('#'):
                continue
            fields: List[str] = line.split('\t')
            if not fields or fields == ['']:
                continue

            phenotype_label_and_metadata: str = fields[0]
            gene_symbols: List[str] = fields[1].split(', ')
            mim_number: str = fields[2].strip()
            cyto_location: str = fields[3].strip()

            phenotype_label, phenotype_mim_number, association_key = '', '', ''
            label_data_with_mim_num = phenotype_label_regex.match(phenotype_label_and_metadata)
            label_data_no_mim_num = phenotype_label_no_mim_regex.match(phenotype_label_and_metadata)

            if label_data_with_mim_num:
                phenotype_label, phenotype_mim_number, association_key = label_data_with_mim_num.groups()
            elif label_data_no_mim_num:
                phenotype_label, association_key = label_data_no_mim_num.groups()
            else:
                print(f'Warning: Failed to parse phenotype label in morbidmap.txt row: {line}', file=sys.stderr)

            if mim_number not in gene_phenotypes:
                gene_phenotypes[mim_number] = {
                    'gene_mim_number': mim_number,
                    'cyto_location': cyto_location,
                    'gene_symbols': gene_symbols,
                    'phenotype_associations': []
                }
            
            gene_phenotypes[mim_number]['phenotype_associations'].append({
                'phenotype_mim_number': phenotype_mim_number,
                'phenotype_label': phenotype_label,
                'phenotype_mapping_info_key': association_key,
                'phenotype_mapping_info_label': MORBIDMAP_PHENOTYPE_MAPPING_KEY_MEANINGS.get(association_key, ''),
            })

        return gene_phenotypes

    def get_phenotype_genes(gene_phenotypes: Dict[str, Dict]) -> Dict[str, List[Dict[str, str]]]:
        """Get Disease->Gene relationships"""
        phenotype_genes: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for gene_mim, gene_data in gene_phenotypes.items():
            for assoc in gene_data['phenotype_associations']:
                p_mim, p_lab, p_map_key, p_map_lab = assoc['phenotype_mim_number'], assoc['phenotype_label'], \
                    assoc['phenotype_mapping_info_key'], assoc['phenotype_mapping_info_label']
                if not p_mim:  # not an association to another MIM; ignore
                    continue
                phenotype_genes[p_mim].append({
                    'gene_id': gene_mim, 'phenotype_label': p_lab, 'mapping_key': p_map_key,
                    'mapping_label': p_map_lab})
        return phenotype_genes


def get_morbidmap_file_path() -> str:
    """Get the path to the morbidmap file, trying both .txt and .tsv extensions."""
    txt_path = DATA_DIR / 'morbidmap.txt'
    tsv_path = DATA_DIR / 'morbidmap.tsv'
    
    if os.path.exists(txt_path):
        return str(txt_path)
    elif os.path.exists(tsv_path):
        return str(tsv_path)
    else:
        # Return the .txt path as default for error handling
        return str(txt_path)


def extract_gene_phenotype_associations(morbidmap_path: str) -> List[Tuple[str, str]]:
    """Extract gene-phenotype associations from morbidmap file.
    
    Args:
        morbidmap_path: Path to the morbidmap file
        
    Returns:
        List of tuples containing (gene_mim, phenotype_mim)
    """
    # Read and parse morbidmap file
    gene_phenos = parse_morbid_map(read_mim_file_as_lines(morbidmap_path))
    
    # Get phenotype-gene relationships
    pheno_genes = get_phenotype_genes(gene_phenos)
    
    # Flatten the data to get gene-phenotype pairs
    gene_phenotype_pairs: Set[Tuple[str, str]] = set()
    
    for p_mim, assocs in pheno_genes.items():
        for assoc in assocs:
            gene_mim = assoc['gene_id']
            # Only include associations where both gene and phenotype MIM are present
            if gene_mim and p_mim:
                gene_phenotype_pairs.add((gene_mim, p_mim))
    
    # Sort for consistent output
    return sorted(list(gene_phenotype_pairs))


def write_gene_phenotype_tsv(gene_phenotype_pairs: List[Tuple[str, str]], output_path: str) -> None:
    """Write gene-phenotype associations to TSV file.
    
    Args:
        gene_phenotype_pairs: List of (gene_mim, phenotype_mim) tuples
        output_path: Path where to write the TSV file
    """
    # Try to use pandas if available for better TSV handling
    try:
        import pandas as pd
        df = pd.DataFrame(gene_phenotype_pairs, columns=['Gene_MIM', 'Phenotype_MIM'])
        df.to_csv(output_path, sep='\t', index=False)
        print(f"Used pandas to write TSV file")
    except ImportError:
        # Fallback to csv module
        with open(output_path, 'w', newline='') as tsvfile:
            writer = csv.writer(tsvfile, delimiter='\t')
            
            # Write header
            writer.writerow(['Gene_MIM', 'Phenotype_MIM'])
            
            # Write data
            for gene_mim, phenotype_mim in gene_phenotype_pairs:
                writer.writerow([gene_mim, phenotype_mim])
        print(f"Used csv module to write TSV file")


def generate_gene_phenotype_tsv() -> None:
    """Main function to generate gene-phenotypes.tsv file."""
    # Get morbidmap file path
    morbidmap_path = get_morbidmap_file_path()
    
    if not os.path.exists(morbidmap_path):
        raise FileNotFoundError(f"Morbidmap file not found at {morbidmap_path}")
    
    # Extract gene-phenotype associations
    gene_phenotype_pairs = extract_gene_phenotype_associations(morbidmap_path)
    
    # Define output path
    output_path = ROOT_DIR / 'gene-phenotypes.tsv'
    
    # Write TSV file
    write_gene_phenotype_tsv(gene_phenotype_pairs, str(output_path))
    
    print(f"Generated {len(gene_phenotype_pairs)} gene-phenotype associations")
    print(f"Output written to: {output_path}")


if __name__ == '__main__':
    generate_gene_phenotype_tsv()
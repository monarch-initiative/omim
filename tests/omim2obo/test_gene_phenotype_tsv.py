"""Test gene_phenotype_tsv module"""

import tempfile
import os
from pathlib import Path

def test_gene_phenotype_tsv():
    """Test the gene-phenotype TSV generation functionality"""
    
    # Import the module without triggering package-level imports
    import importlib.util
    script_dir = Path(__file__).parent.parent.parent / 'omim2obo'
    spec = importlib.util.spec_from_file_location('gene_phenotype_tsv', script_dir / 'gene_phenotype_tsv.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Create test data
    test_data = """# Test morbidmap data
Alzheimer disease, 104300 (3)\tAPP\t104760\t21q21.3
Bleeding disorder due to defective thromboxane A2 receptor, 605397 (3)\tTBXA2R\t188070\t19p13.3
{Diabetes mellitus, noninsulin-dependent}, 125853 (2)\tINSR\t147670\t19p13.2
Parkinson disease, late-onset, 168600 (1)\tSNCA\t163890\t4q22.1"""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_data)
        input_file = f.name
    
    try:
        # Extract associations
        pairs = module.extract_gene_phenotype_associations(input_file)
        
        # Verify results
        assert len(pairs) == 4, f"Expected 4 associations, got {len(pairs)}"
        
        expected_pairs = [
            ('104760', '104300'),  # APP -> Alzheimer disease
            ('147670', '125853'),  # INSR -> Diabetes mellitus
            ('163890', '168600'),  # SNCA -> Parkinson disease
            ('188070', '605397'),  # TBXA2R -> Bleeding disorder
        ]
        
        for expected in expected_pairs:
            assert expected in pairs, f"Expected pair {expected} not found in results"
        
        # Test TSV writing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_file = f.name
        
        module.write_gene_phenotype_tsv(pairs, output_file)
        
        # Verify TSV content
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 5, f"Expected 5 lines (header + 4 data), got {len(lines)}"
        assert lines[0].strip() == "Gene_MIM\tPhenotype_MIM", "Header incorrect"
        
        # Clean up
        os.unlink(output_file)
        
        print("test_gene_phenotype_tsv passed!")
        return True
        
    finally:
        os.unlink(input_file)

if __name__ == '__main__':
    test_gene_phenotype_tsv()
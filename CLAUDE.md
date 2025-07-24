# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT: Always read README.md first for detailed context, curator instructions, and the most up-to-date project information before making any changes or answering questions about this codebase.**

## Overview

This repository transforms OMIM (Online Mendelian Inheritance in Man) data into semantic web formats for integration into the Mondo Disease Ontology. It downloads OMIM data files, parses them, creates disease-gene associations with appropriate relationship ontology predicates, and generates RDF/OWL ontology files.

## Common Commands

**Build Commands:**
- `make all` - Creates all release artifacts (omim.ttl, omim.sssom.tsv, omim.owl, mondo-omim-genes.robot.tsv)
- `make omim.ttl` or `python -m omim2obo` - Main build command (downloads data and generates omim.ttl)
- `python -m omim2obo --use-cache` - Offline build using cached data files
- `sh run.sh make all` - Runs build in Docker container using ODK

**Development Commands:**
- `make install` - Install Python dependencies
- `make test` - Run unit tests using Python unittest
- `python -m pytest tests/` - Run specific tests
- `make scrape y=2021 m=5` - Web scraping for OMIM statistics (YYYY/MM format)
- `make get-pmids` - Extract OMIM codes and PMIDs

**Lint/Type Check Commands:**
When making code changes, run basic Python validation:
- `python -m py_compile omim2obo/main.py` - Check syntax
- `python -m omim2obo.parsers.omim_txt_parser` - Test parser modules

## Architecture

### Core Processing Flow

1. **Data Download**: Retrieves OMIM files (mimTitles.txt, morbidmap.txt, mim2gene.txt) and HGNC data
2. **Parsing**: Transforms text files into structured data using specialized parsers
3. **Relationship Mapping**: Applies MORBIDMAP phenotype mapping keys to Relationship Ontology predicates:
   - Key 2 → RO:0003303 (causes condition)
   - Key 3 → RO:0004013/RO:0004003 (causal germline mutation relationships)
   - Key 4 → RO:0003304 (contributes to condition)
   - Multiple associations → RO:0003302 (causes or contributes to condition)
4. **Quality Control**: Generates review cases for curator attention
5. **Output Generation**: Creates RDF/OWL files and ROBOT templates

### Key Modules

**`omim2obo/main.py`**: Core processing logic with `omim2obo()` function
- Entry point for all data transformation
- Contains disease-gene association logic with curator override handling
- Manages RDF graph construction and serialization

**`omim2obo/parsers/`**: Specialized parsers for OMIM data formats
- `omim_txt_parser.py`: Handles OMIM text file formats (mimTitles, morbidmap, etc.)
- `omim_entry_parser.py`: Processes individual entries and handles capitalization rules

**`omim2obo/config.py`**: Configuration management and file paths
- Defines data directories and output paths
- Manages environment variables and API configuration

**`omim2obo/namespaces.py`**: RDF namespace definitions for extensive ontology coverage

### Curator Override System

Three key TSV files allow manual curation interventions:
- `data/exclusions-disease-gene.tsv`: Exclude specific disease-gene associations
- `data/protected-disease-gene.tsv`: Protect associations from automated removal
- `data/known_capitalizations.tsv`: Override automatic capitalization

## Data Processing Patterns

### OMIM Entry Types
- `*` (GENE) and `+` (HAS_AFFECTED_FEATURE): Gene entries with SO:0000704 classification
- `#` (PHENOTYPE): Disease/phenotype entries with biolink:Disease category
- `%` (HERITABLE_PHENOTYPIC_MARKER): Also classified as biolink:Disease
- NULL (SUSPECTED): Excluded with MONDO:excludeTrait

### Disease-Gene Association Rules
- Single association with mapping key 3 + definitive phenotype label → Causal germline mutation (RO:0004013/RO:0004003)
- Multiple associations or non-definitive → Generic cause/contribute relationship (RO:0003302)
- Curator exclusions override automated logic

### Review Case Generation
The system flags edge cases in `review.tsv`:
- **D2G: digenic**: Single gene entries incorrectly labeled as digenic
- **D2G: self-referential**: Complex circular reference patterns
- **D2G: somatic**: Somatic vs germline mutation conflicts

## Configuration Files

**Core Configuration:**
- `.env` (from `.env.example`): API keys and environment settings
- `data/dipper/curie_map.yaml`: CURIE to URI mappings for RDF namespaces
- `data/metadata.sssom.yml`: SSSOM mapping metadata

**Build Configuration:**
- `makefile`: Build targets and dependency management
- `requirements.txt`: Python dependencies
- `pytest.ini`: Test configuration

## Development Notes

### RDF Graph Construction
- Uses custom `DeterministicBNode` class for reproducible builds
- All relationship assertions include evidence annotations
- Ontology IRI: `http://purl.obolibrary.org/obo/mondo/omim.owl`
- Version IRI follows pattern: `http://purl.obolibrary.org/obo/mondo/releases/{YYYY-MM-DD}/omim.owl`

### Testing
- Unit tests in `tests/` directory with sample OMIM entry JSON files
- Test different OMIM entry types (%, *, +, #, ^, NULL)
- Focus on parser logic and utility functions

### Error Handling
- Structured logging with appropriate levels for debugging
- Review case system captures problematic associations for curator review
- Validation of required fields and data integrity checks

### Docker Integration
- ODK (Ontology Development Kit) based containerized workflow
- `run.sh` script provides Docker wrapper for build commands
- Ensures reproducible builds across environments
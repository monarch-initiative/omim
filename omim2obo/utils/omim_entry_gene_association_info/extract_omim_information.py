import pandas as pd
import requests
import re
import time
from dotenv import load_dotenv
import os


load_dotenv()

OMIM_API_KEY = os.getenv("API_KEY")
if not OMIM_API_KEY:
    raise ValueError("OMIM_API_KEY not found in environment or .env file")

OMIM_URL = "https://api.omim.org/api/entry"
INPUT_FILE = "mondo_mim-medgen_evidence.tsv"
OUTPUT_FILE = "mondo_mim-medgen_evidence_with-omim-info.tsv"


def extract_omim_ids(xrefs: str):
    return re.findall(r'(OMIM(?:PS)?:\d+)', xrefs)


def get_omim_data(mim_number: str):
    url = f"{OMIM_URL}?mimNumber={mim_number}&apiKey={OMIM_API_KEY}&format=json&include=geneMap,externalLinks,text,editHistory"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        entry = data["omim"]["entryList"][0]["entry"]

        # OMIM Entry prefix, denotes type of OMIM entry https://omim.org/help/faq#1_3
        prefix = entry["prefix"]

        # Text
        text_summary = ""
        for section in entry.get("textSectionList", []):
            sec = section.get("textSection", {})
            if sec.get("textSectionTitle") == "Text":
                text_summary = sec.get("textSectionContent", "").replace("\n", " ").strip()
                break

        # externalLinks for hgncID
        external_links = entry.get("externalLinks", {})
        hgnc_id = external_links.get("hgnc", "")

        # phenotypeMapList (may be multiple)
        phenotypes = []
        for pheno_entry in entry.get("phenotypeMapList", []):
            pheno = pheno_entry.get("phenotypeMap", {})
            pheno_mim = pheno.get("phenotypeMimNumber", "")
            if pheno.get("phenotypeMimNumber", ""):
                pheno_url = f'=HYPERLINK("https://omim.org/entry/{pheno_mim}", "https://omim.org/entry/{pheno_mim}")'
            else:
                pheno_url = ""
            phenotypes.append({
                "phenotype": pheno.get("phenotype", ""),
                "phenotypeMimNumber": pheno.get("phenotypeMimNumber", ""),
                "geneMimNumber": pheno.get("mimNumber", ""),
                "omimURL": pheno_url,
                "phenotypeMappingKey": pheno.get("phenotypeMappingKey", ""),
                "approvedGeneSymbols": pheno.get("approvedGeneSymbols", "")

            })

        return {
            "omimEntryPrefix": prefix,
            "textSummary": text_summary,
            "hgncID": hgnc_id,
            "phenotypes": phenotypes
        }

    except Exception as e:
        print(f"[ERROR] OMIM {mim_number}: {e}")
        return {
            "omimEntryPrefix": "",
            "textSummary": "",
            "hgncID": "",
            "phenotypes": []
        }

def main():
    df = pd.read_csv(INPUT_FILE, sep="\t")
    output_rows = []

    for _, row in df.iloc[1:].iterrows():
        mondo_id = row['?sub']
        mondo_label = row['?label']
        maintain_gene_annotation = row['should have gene annotation']

        xrefs = str(row['?xrefs'])
        omim_ids = extract_omim_ids(xrefs)

        for omim_curie in omim_ids:
            prefix, mim_number = omim_curie.split(":")
            omim_data = get_omim_data(mim_number)

            # Each phenotype becomes its own row
            for p in omim_data["phenotypes"] or [{}]:
                output_rows.append({
                    "mondo_id": mondo_id,
                    "mondo_label": mondo_label,
                    "xrefs": xrefs,
                    "should have gene annotation": maintain_gene_annotation,
                    "extracted_omim_curie": omim_curie,
                    "phenotype": p.get("phenotype", ""),
                    "omim_prefix": omim_data["omimEntryPrefix"],
                    "phenotypeMimNumber": p.get("phenotypeMimNumber", ""),
                    "geneMimNumber": p.get("geneMimNumber", ""),
                    "omimURL": p.get("omimURL", ""),
                    "phenotypeMappingKey": p.get("phenotypeMappingKey", ""),
                    "approvedGeneSymbols": p.get("approvedGeneSymbols", ""),
                    "hgncID": omim_data["hgncID"],
                    "textSectionContent": omim_data["textSummary"]
                })

            time.sleep(0.5)

    out_df = pd.DataFrame(output_rows)
    out_df.to_csv(OUTPUT_FILE, sep="\t", index=False)
    print(f"Output written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

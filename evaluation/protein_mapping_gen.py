import pandas as pd
import requests
import re
import time

# Map common organism names to UniProt standard format
ORGANISM_MAPPING = {
    "Human": "Homo sapiens",
    "Mouse": "Mus musculus",
    "C. elegans": "Caenorhabditis elegans",
    "Drosophila melanogaster": "Drosophila melanogaster",
    "Yeast": "Saccharomyces cerevisiae"
}

def clean_protein_name(name):
    # Remove anything in parentheses, special characters, and excess spaces
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^a-zA-Z0-9\s\-]", "", name)
    return name.strip()

def get_uniprot_data(protein, organism):
    query = f'"{protein}" AND organism_name:"{organism}"'
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": query,
        "fields": "gene_primary,accession",
        "format": "json",
        "size": 1
    }
    response = requests.get(url, params=params)
    time.sleep(0.5)  # Respect UniProt's rate limit

    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            result = data["results"][0]
            gene_name = result.get("genes", [{}])[0].get("geneName", {}).get("value")
            accession = result.get("primaryAccession")
            return gene_name if gene_name else "Only accession ID found", accession
    # return "Not found", "Not found"

def process_csv(input_path, output_path):
    df = pd.read_csv(input_path)

    gene_symbol_list = []
    accession_list = []

    for index, row in df.iterrows():
        proteins_raw = str(row.get("Proteins", ""))
        organism_raw = str(row.get("Organism", ""))
        organism = ORGANISM_MAPPING.get(organism_raw.strip(), organism_raw.strip())

        proteins = re.split(r"[\n,]+", proteins_raw)
        proteins = [clean_protein_name(p) for p in proteins if p.strip()]

        gene_symbols = []
        accessions = []

        for protein in proteins:
            gene, acc = get_uniprot_data(protein, organism)
            gene_symbols.append(gene)
            accessions.append(acc)

        gene_symbol_list.append(", ".join(gene_symbols))
        accession_list.append(", ".join(accessions))

    df["Gene Symbols"] = gene_symbol_list
    df["Accession IDs"] = accession_list

    df.to_csv(output_path, index=False)
    print(f"Updated file saved to: {output_path}")

# Example usage:
process_csv("PARSR.csv", "test.csv")

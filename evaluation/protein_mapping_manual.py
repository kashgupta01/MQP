import pandas as pd
import requests
import re

# Load the CSV
df = pd.read_csv("manual_curation.csv", encoding = 'ISO-8859-1')

# Organism mapping to UniProt-friendly names
organism_map = {
    "Human": "Homo sapiens",
    "Mouse": "Mus musculus",
    "C. elegans": "Caenorhabditis elegans",
    "Drosophila": "Drosophila melanogaster"
}

# Preprocess proteins: remove line breaks and normalize separators
df["Proteins"] = df["Proteins"].fillna("").apply(lambda x: re.sub(r'\s*\n\s*', ', ', x).strip())

# Convert to standardized organism names
df["Organism"] = df["Organism"].map(organism_map).fillna(df["Organism"])

# Function to get gene symbol, fallback to accession ID
def get_gene_symbol_or_accession(protein_name, organism):
    base_url = "https://rest.uniprot.org/uniprotkb/search"
    # Sanitize the name (remove anything in parentheses or after comma)
    clean_name = re.split(r"\(|,", protein_name.strip())[0].strip()
    query = f'("{clean_name}" AND organism_name:"{organism}")'
    
    params = {
        "query": query,
        "fields": "gene_primary",
        "format": "json",
        "size": 1
    }

    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            results = response.json()
            if "results" in results and results["results"]:
                result = results["results"][0]
                primary_gene = result.get("genes", [{}])[0].get("geneName", {}).get("value")
                accession = result.get("primaryAccession")
                
                if primary_gene:
                    return primary_gene
                elif accession:
                    return f"Only accession ID found: {accession}"
        return "Not found"
    except Exception as e:
        return f"Error: {e}"

# Apply gene symbol retrieval for each protein in a row
def map_proteins_to_symbols(row):
    protein_list = [p.strip() for p in row["Proteins"].split(",") if p.strip()]
    gene_symbols = [get_gene_symbol_or_accession(p, row["Organism"]) for p in protein_list]
    return ", ".join(gene_symbols)

# Run the mapping
df["Gene Symbols"] = df.apply(map_proteins_to_symbols, axis=1)

# Save to a new CSV
df.to_csv("manual_curation_with_gene_symbols_cleaned.csv", index=False)
print("Updated CSV with gene symbols saved.")

import pandas as pd
import requests
import time

# Load your data
df = pd.read_csv("manual_curation.csv", encoding = "ISO-8859-1")

# Replace line breaks with commas in the Proteins column
df["Proteins"] = df["Proteins"].fillna("").apply(lambda x: x.replace("\n", ", ").replace("\r", ""))

# Function to query UniProt for a protein name and organism
def get_gene_symbol(protein_name, organism):
    base_url = "https://rest.uniprot.org/uniprotkb/search"
    query = f'("{protein_name}" AND organism_name:{organism})'
    params = {
        "query": query,
        "fields": "gene_primary",
        "format": "json",
        "size": 1
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            results = response.json()
            if "results" in results and results["results"]:
                entry = results["results"][0]
                gene_name = entry.get("genes", [{}])[0].get("geneName", {}).get("value")
                accession_id = entry.get("primaryAccession", "Not found")
                if gene_name:
                    return gene_name, ""
                else:
                    return "Only accession ID found", accession_id
    except Exception as e:
        print(f"Error processing {protein_name} from {organism}: {e}")
    
    return "Not found", "Not found"

# Extract gene symbols for each protein
gene_symbols = []
accession_ids = []

for _, row in df.iterrows():
    proteins = [p.strip() for p in row["Proteins"].split(",")]
    organism = row["Organism"]
    
    row_genes = []
    row_accessions = []
    for protein in proteins:
        gene, acc = get_gene_symbol(protein, organism)
        row_genes.append(gene)
        row_accessions.append(acc)
    
    gene_symbols.append(", ".join(row_genes))
    accession_ids.append(", ".join([a for a in row_accessions if a]))

# Add to DataFrame
df["Gene Symbols"] = gene_symbols
df["Accession IDs"] = accession_ids

# Save to new CSV
df.to_csv("manual_curation_with_gene_symbols.csv", index=False)
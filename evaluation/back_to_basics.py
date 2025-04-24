import pandas as pd
import numpy as np  
import re 
import requests 
import time 
import urllib.parse

manual_df = pd.read_csv("manual_curation.csv", encoding = "ISO-8859-1")
gpt41_df = pd.read_csv("all_62_complexes\gpt-4-1_v2_parsed.csv")

manual_df["Proteins"] = manual_df["Proteins"].fillna("").apply(lambda x: x.replace("\n", "; ").replace("\r", ""))
manual_df["Proteins"] = manual_df["Proteins"].apply(lambda x: re.sub(r"\s*\(.*?\)", "", x))

def standardize_organism(org):
    if isinstance(org, str):
        org = org.lower()
        if 'human' in org or 'human (homo sapiens)' in org or 'Human (Homo sapiens) – the 13 subunit eIF3 complex is most prominent in humans.' in org or 'homo sapiens (human)' in org:
            return 'Homo Sapiens (Human)'
        elif 'mouse' in org:
            return 'Mus Musculus (Mouse)'
        elif 'c. elegans' in org or 'caenorhabditis' in org or 'caenorhabditis elegans (c. elegans)' in org:
            return 'Caenorhabditis Elegans'
        elif 'drosophila' in org or 'd. melanogaster' in org:
            return 'Drosophila Melanogaster (Fruit Fly)'
        elif 'yeast' in org or 'saccharomyces' in org or 'saccharomyces cerevisiae (budding yeast)':
            return "Saccharomyces cerevisiae (strain ATCC 204508 / S288c) (Baker's yeast)"
        return org.strip()
    return org

manual_df['Organism'] = manual_df['Organism'].apply(standardize_organism)
gpt41_df['Organism'] = gpt41_df['Organism'].apply(standardize_organism)

def query_uniprot(protein, organism):
    url = "https://rest.uniprot.org/uniprotkb/search"
    query = f'{protein} AND organism_name:"{organism}"'
    params = {
        "query": query,
        "fields": "accession",
        "format": "json",
        "size": 1
    }
    full_url = f"{url}?{urllib.parse.urlencode(params)}"

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            if len(lines) > 1:
                return lines[1].split("\t")[0]
        return "Not Found"
    except Exception as e:
        print(f"Error querying {protein} from {organism}: {e}")
        return "Error"

# Apply protein mapping per row
def map_proteins_to_uniprot(row):
    proteins = [p.strip() for p in row['Proteins'].split(";") if p.strip()]
    organism = row['Organism']
    accessions = []
    for protein in proteins:
        acc = query_uniprot(protein, organism)
        accessions.append(acc)
        time.sleep(0.5)  # Be respectful to UniProt API
    return "; ".join(accessions)

# Map both dataframes
print("Mapping proteins in manual_df...")
manual_df['Accession_Mapped'] = manual_df.apply(map_proteins_to_uniprot, axis=1)

print("Mapping proteins in gpt41_df...")
gpt41_df['Accession_Mapped'] = gpt41_df.apply(map_proteins_to_uniprot, axis=1)

# Save output
manual_df.to_csv("manual_with_uniprot_mapping.csv", index=False)
gpt41_df.to_csv("gpt41_with_uniprot_mapping.csv", index=False)
print("Mapping completed and files saved.")


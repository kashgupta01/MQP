import pandas as pd
import numpy as np  
import re 
import requests 
import time 
import urllib.parse

#manual_df = pd.read_csv("manual_curation.csv", encoding = "ISO-8859-1")
claude_opus_df = pd.read_csv("all_62_complexes\claude-3-opus_v2_parsed.csv")

#manual_df["Proteins"] = manual_df["Proteins"].fillna("").apply(lambda x: x.replace("\n", "; ").replace("\r", ""))
#manual_df["Proteins"] = manual_df["Proteins"].apply(lambda x: re.sub(r"\s*\(.*?\)", "", x))

claude_opus_df["Proteins"] = claude_opus_df["Proteins"].apply(lambda x: re.sub(r"\s*[\(\[].*?[\)\]]", "", x))



def standardize_organism(org):
    if isinstance(org, str):
        org = org.lower()
        if 'human' in org or 'human (homo sapiens)' in org or 'Human (Homo sapiens) – the 13 subunit eIF3 complex is most prominent in humans.' in org or 'homo sapiens (human)' in org:
            return 'Homo Sapiens'
        elif 'mouse' in org:
            return 'Mus Musculus'
        elif 'c. elegans' in org or 'caenorhabditis' in org or 'caenorhabditis elegans (c. elegans)' in org:
            return 'Caenorhabditis Elegans'
        elif 'drosophila' in org or 'd. melanogaster' in org:
            return 'Drosophila Melanogaster'
        elif 'yeast' in org or 'saccharomyces' in org or 'saccharomyces cerevisiae (budding yeast)':
            return "Saccharomyces cerevisiae"
        return org.strip()
    return org

#manual_df['Organism'] = manual_df['Organism'].apply(standardize_organism)
claude_opus_df['Organism'] = claude_opus_df['Organism'].apply(standardize_organism)

def query_uniprot(protein, organism):
    url = "https://rest.uniprot.org/uniprotkb/search"
    query = f'protein_name:"{protein}" AND organism_name:"{organism}"'
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
            data = response.json()
            if data.get("results"):
                return data["results"][0]["primaryAccession"]
            # Fallback to gene_exact if protein_name fails
            fallback_query = f'gene_exact:{protein} AND organism_name:"{organism}"'
            params["query"] = fallback_query
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    return data["results"][0]["primaryAccession"]
                else:
                    return "Not Found"
        else:
            print(f"Request failed: {response.status_code}")
            return "Error"
    except Exception as e:
        print(f"Error querying {protein} from {organism}: {e}")
        return "Error"

# Apply protein mapping per row
failed_queries = []
def map_proteins_to_uniprot(row):
    proteins = [p.strip() for p in row['Proteins'].split(";") if p.strip()]
    organism = row['Organism']
    accessions = []
    for protein in proteins:
        acc = query_uniprot(protein, organism)
        if acc is None: 
            acc = "Not Found"
        if acc in ["Error", "Not Found"]: 
            failed_queries.append((proteins, organism))
        accessions.append(acc)
        time.sleep(0.5)  # Be respectful to UniProt API
    return "; ".join(accessions)

# Map both dataframes
#print("Mapping proteins in manual_df...")
#manual_df['Accession_Mapped'] = manual_df.apply(map_proteins_to_uniprot, axis=1)

print("Mapping proteins in claude_opus_df...")
claude_opus_df['Accession_Mapped'] = claude_opus_df.apply(map_proteins_to_uniprot, axis=1)

# Save output
#manual_df.to_csv("manual_mapping2.csv", index=False)
claude_opus_df.to_csv("claude_opus_mapping.csv", index=False)
print("Mapping completed and files saved.")

if failed_queries:
    pd.DataFrame(failed_queries, columns=["Protein", "Organism"]).to_csv("failed_queries_opus.csv", index=False)
    print(f"{len(failed_queries)} queries failed. Saved to 'failed_queries_opus.csv'.")
else:
    print("All queries succeeded!")
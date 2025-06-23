import pandas as pd
import requests
import time
import re

def normalize_proteins(protein_str):
    if pd.isna(protein_str):
        return []
    proteins = re.split(r';|,|\n', protein_str)
    cleaned = []
    for protein in proteins:
        protein = re.sub(r'\(.*?\)', '', protein)
        protein = protein.lower().strip()
        protein = re.sub(r'[^a-z0-9\s\-]', '', protein)
        if protein:
            cleaned.append(protein)
    return cleaned

def normalize_organism(org):
    if pd.isna(org):
        return None
    org = org.lower()
    if "human" in org:
        return "Homo sapiens"
    elif "mouse" in org:
        return "Mus musculus"
    elif "rat" in org:
        return "Rattus norvegicus"
    elif "celegans" in org or "c elegans" in org:
        return "Caenorhabditis elegans"
    elif "drosophila" in org:
        return "Drosophila melanogaster"
    elif "yeast" in org or "saccharomyces" in org:
        return "Saccharomyces cerevisiae"
    else:
        return None

def query_uniprot(protein_name, organism=None):
    query = f'name:"{protein_name}"'
    if organism:
        query += f' AND organism_name:"{organism}"'
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": query,
        "fields": "accession",
        "format": "tsv",
        "size": 1
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200 and "accession" in response.text:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception as e:
        print(f"Error for {protein_name}: {e}")
    return None

def get_best_accessions(protein_list, organism):
    accessions = []
    for protein in protein_list:
        acc = query_uniprot(protein, organism)
        if not acc:
            simplified = " ".join(protein.split()[:2])
            acc = query_uniprot(simplified, organism)
        if not acc:
            acc = query_uniprot(protein)  # fallback no organism
        accessions.append(acc if acc else "Not Found")
        time.sleep(0.5)
    return accessions

def map_uniprot(df):
    df["Normalized Proteins"] = df["Proteins"].apply(normalize_proteins)
    df["Normalized Organism"] = df["Organism"].apply(normalize_organism)
    df["UniProt Accessions"] = df.apply(
        lambda row: get_best_accessions(row["Normalized Proteins"], row["Normalized Organism"]),
        axis=1
    )
    return df

# Load and map both datasets
llm_df = pd.read_csv("all_62_complexes\gpt-4-1_v2_parsed.csv")
manual_df = pd.read_csv("manual_curation.csv", encoding='ISO-8859-1')

llm_df = map_uniprot(llm_df)
manual_df = map_uniprot(manual_df)

llm_df.to_csv("llm_with_uniprot_organism.csv", index=False)
manual_df.to_csv("manual_with_uniprot_organism.csv", index=False)

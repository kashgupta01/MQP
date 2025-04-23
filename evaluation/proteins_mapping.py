import pandas as pd
import requests
import time

# Define UniProt query function
def get_gene_symbol(protein_name):
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": protein_name,
        "fields": "gene_names",
        "format": "tsv",
        "size": 1
    }
    try:
        response = requests.get(url, params=params)
        if response.ok:
            lines = response.text.strip().split('\n')
            if len(lines) > 1:
                gene_info = lines[1].split('\t')[0]
                return gene_info.split()[0]  # Return first gene symbol
    except Exception as e:
        print(f"Error for {protein_name}: {e}")
    return "N/A"

# Load your CSV file (update filename accordingly)
df = pd.read_csv("manual_curation.csv", encoding='ISO-8859-1')
print(df.columns)
df_proteins = df["Proteins"]
# Assuming the column is named 'Protein'; change if necessary
df["Abbreviation"] = df["Proteins"].apply(lambda name: get_gene_symbol(name.split(" (")[0]))

# Save the new CSV
df.to_csv("protein_list_with_abbreviations.csv", index=False)

print("Done! Output saved to 'protein_list_with_abbreviations.csv'")

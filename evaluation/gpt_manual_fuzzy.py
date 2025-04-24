import pandas as pd
import re
from fuzzywuzzy import fuzz

# Function to clean and normalize protein names
def clean_protein_list(protein_str):
    if pd.isna(protein_str):
        return []
    protein_str = re.sub(r'[^\w\s\-]', '', protein_str.lower())
    return [p.strip() for p in re.split(r'\s*;\s*|\s*,\s*|\r\n|\n', protein_str) if p.strip()]

# Function to standardize organism names
def standardize_organism(org):
    if isinstance(org, str):
        org = org.lower()
        if 'human' in org:
            return 'homo sapiens'
        elif 'mouse' in org:
            return 'mus musculus'
        elif 'c. elegans' in org or 'caenorhabditis' in org:
            return 'caenorhabditis elegans'
        elif 'drosophila' in org:
            return 'drosophila melanogaster'
        elif 'yeast' in org or 'saccharomyces' in org:
            return 'saccharomyces cerevisiae'
        return org.strip()
    return org

# Fuzzy similarity score for protein sets
def fuzzy_set_similarity(list1, list2, threshold=80):
    if not list1 or not list2:
        return 0.0
    matches = 0
    for item1 in list1:
        if any(fuzz.token_sort_ratio(item1, item2) >= threshold for item2 in list2):
            matches += 1
    return matches / max(len(list1), len(list2))

# Main function
def compare_proteins_organisms(llm_path, manual_path):
    llm_df = pd.read_csv(llm_path)
    manual_df = pd.read_csv(manual_path, encoding='latin1')

    llm_df['Proteins_clean'] = llm_df['Proteins'].apply(clean_protein_list)
    llm_df['Organism_clean'] = llm_df['Organism'].apply(standardize_organism)

    manual_df['Proteins_clean'] = manual_df['Proteins'].apply(clean_protein_list)
    manual_df['Organism_clean'] = manual_df['Organism'].apply(standardize_organism)

    merged = pd.merge(llm_df, manual_df, on="Complex Name", suffixes=('_llm', '_manual'))

    merged['Protein_similarity'] = merged.apply(
        lambda row: fuzzy_set_similarity(row['Proteins_clean_llm'], row['Proteins_clean_manual']), axis=1)

    merged['Organism_match'] = merged.apply(
        lambda row: row['Organism_clean_llm'] == row['Organism_clean_manual'], axis=1)

    accuracy = merged.groupby("Technique").agg({
        'Protein_similarity': 'mean',
        'Organism_match': 'mean'
    }).rename(columns={"Organism_match": "Organism_accuracy"})

    return accuracy

# Example usage
if __name__ == "__main__":
    result = compare_proteins_organisms("all_62_complexes\gpt-4-1_v2_parsed.csv", "manual_curation.csv")
    print(result)

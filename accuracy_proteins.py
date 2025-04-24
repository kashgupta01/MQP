import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher

# Load the data
manual_df = pd.read_csv("manual_mapping2.csv")
gpt41_df = pd.read_csv("gpt41_mapping2.csv")
gpt40_df = pd.read_csv("gpt4o_mapping.csv")
opus_df = pd.read_csv("claude_opus_mapping.csv")
sonnet_df = pd.read_csv("claude_sonnet_mapping.csv")

# Clean column names
for df in [manual_df, gpt41_df, gpt40_df, opus_df, sonnet_df]:
    df.columns = [col.strip() for col in df.columns]

# Function to process accession strings into sets
def process_accessions(cell):
    if pd.isna(cell) or cell.strip() == "":
        return set()
    return set([acc.strip() for acc in cell.split(";") if acc.strip()])

# Function to compute partial match using similarity ratio
def is_partial_match(set1, set2, threshold=0.8):
    matches = 0
    for acc1 in set1:
        for acc2 in set2:
            if SequenceMatcher(None, acc1, acc2).ratio() >= threshold:
                matches += 1
                break
    return matches > 0

# Accuracy analysis function with fuzzy matching
def compare_accessions(manual_df, pred_df, technique_col="Technique", threshold=0.8):
    results = []
    techniques = pred_df[technique_col].dropna().unique()

    for tech in techniques:
        pred_sub = pred_df[pred_df[technique_col] == tech]
        total = 0
        exact_correct = 0
        partial_correct = 0

        for _, pred_row in pred_sub.iterrows():
            complex_name = pred_row["Complex Name"]
            pred_accessions = process_accessions(pred_row.get("Accession_Mapped", ""))
            manual_row = manual_df[manual_df["Complex Name"] == complex_name]

            if manual_row.empty:
                continue

            manual_accessions = process_accessions(manual_row.iloc[0].get("Accession_Mapped", ""))
            if not manual_accessions:
                continue

            total += 1
            if pred_accessions == manual_accessions:
                exact_correct += 1
            elif is_partial_match(pred_accessions, manual_accessions, threshold):
                partial_correct += 1

        exact_acc = exact_correct / total if total > 0 else 0
        partial_acc = (exact_correct + partial_correct) / total if total > 0 else 0

        results.append({
            "Technique": tech,
            "Exact Accuracy": exact_acc,
            "Partial Match Accuracy": partial_acc,
            "Total": total,
            "Exact Matches": exact_correct,
            "Partial Matches": partial_correct
        })

    return pd.DataFrame(results)

# Run comparison
print("GPT41 Accuracy:\n", compare_accessions(manual_df, gpt41_df))
print("GPT4o Accuracy:\n", compare_accessions(manual_df, gpt40_df))
print("Opus Accuracy:\n", compare_accessions(manual_df, opus_df))
print("Sonnet Accuracy:\n", compare_accessions(manual_df, sonnet_df))

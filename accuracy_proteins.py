import pandas as pd
import numpy as np 
from difflib import SequenceMatcher
import matplotlib.pyplot as plt

# Load the data
manual_df = pd.read_csv("manual_mapping2.csv")
gpt41_df = pd.read_csv("gpt41_mapping2.csv")
gpt40_df = pd.read_csv("gpt4o_mapping.csv")
opus_df = pd.read_csv("claude_opus_mapping.csv")
sonnet_df = pd.read_csv("claude_sonnet_mapping.csv")

# Normalize column names and complex names across all datasets
for df in [manual_df, gpt41_df, gpt40_df, opus_df, sonnet_df]:
    df.columns = [col.strip() for col in df.columns]
    df["Complex Name"] = df["Complex Name"].astype(str).str.strip().str.lower()

# Function to process accession strings into sets
def process_accessions(cell):
    if pd.isna(cell) or cell.strip() == "":
        return set()
    return set(acc.strip() for acc in cell.split(";") if acc.strip())

# Fuzzy matching for partial overlap
def is_partial_match(set1, set2, threshold=0.8):
    for acc1 in set1:
        for acc2 in set2:
            if SequenceMatcher(None, acc1, acc2).ratio() >= threshold:
                return True
    return False

# Accuracy analysis function with exact and fuzzy match
def compare_accessions(manual_df, pred_df, technique_col="Technique", threshold=0.60):
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
                print(f"Missing in manual: {complex_name}")
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

# Run comparisons
print("GPT41 Accuracy:\n", compare_accessions(manual_df, gpt41_df))
print("GPT4o Accuracy:\n", compare_accessions(manual_df, gpt40_df))
print("Opus Accuracy:\n", compare_accessions(manual_df, opus_df))
print("Sonnet Accuracy:\n", compare_accessions(manual_df, sonnet_df))



def label_model(df, model_name):
    df = df.copy()
    df["Model"] = model_name
    df["Additional Partial Accuracy"] = df["Partial Match Accuracy"] - df["Exact Accuracy"]
    return df

# Run and label all model comparisons
gpt41_labeled = label_model(compare_accessions(manual_df, gpt41_df), "GPT-4-1")
gpt40_labeled = label_model(compare_accessions(manual_df, gpt40_df), "GPT-4o")
opus_labeled = label_model(compare_accessions(manual_df, opus_df), "Claude Opus")
sonnet_labeled = label_model(compare_accessions(manual_df, sonnet_df), "Claude Sonnet")
'''
models_data = {
    "GPT-4-1": gpt41_labeled,
    "GPT-4o": gpt40_labeled,
    "Claude Opus": opus_labeled,
    "Claude Sonnet": sonnet_labeled
}

# Plot function: stacked bars + data labels
def plot_model_accuracy(df, model_name):
    techniques = df["Technique"].tolist()
    exact = df["Exact Accuracy"].tolist()
    additional = df["Additional Partial Accuracy"].tolist()
    x = range(len(techniques))
    colors = ["#FF6961", "#61A8FF"]  # Exact: Blue, Additional Partial: Green

    fig, ax = plt.subplots(figsize=(8, 6))
    bars1 = ax.bar(x, exact, label="Exact Match Accuracy", color=colors[0])
    bars2 = ax.bar(x, additional, bottom=exact, label="Additional Partial Accuracy", color=colors[1])

    # Add data labels
    for i in range(len(x)):
        ax.text(x[i], exact[i]/2, f"{exact[i]:.2f}", ha='center', va='center', fontsize=10, color='white')
        ax.text(x[i], exact[i] + additional[i]/2, f"{additional[i]:.2f}", ha='center', va='center', fontsize=10, color='white')

    ax.set_xticks(x)
    ax.set_xticklabels(techniques, fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title(f"{model_name} Accuracy by Prompt Technique", fontsize=14, weight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(f"{model_name.replace(' ', '_').lower()}_accuracy.png")
    plt.show()

# Generate plots
for model, df in models_data.items():
    plot_model_accuracy(df, model)
'''


# Average accuracy results per model
averaged_data = pd.DataFrame([
    {
        "Model": "GPT-4-1",
        "Exact Accuracy": gpt41_labeled["Exact Accuracy"].mean(),
        "Partial Match Accuracy": gpt41_labeled["Partial Match Accuracy"].mean()
    },
    {
        "Model": "GPT-4o",
        "Exact Accuracy": gpt40_labeled["Exact Accuracy"].mean(),
        "Partial Match Accuracy": gpt40_labeled["Partial Match Accuracy"].mean()
    },
    {
        "Model": "Claude Opus",
        "Exact Accuracy": opus_labeled["Exact Accuracy"].mean(),
        "Partial Match Accuracy": opus_labeled["Partial Match Accuracy"].mean()
    },
    {
        "Model": "Claude Sonnet",
        "Exact Accuracy": sonnet_labeled["Exact Accuracy"].mean(),
        "Partial Match Accuracy": sonnet_labeled["Partial Match Accuracy"].mean()
    }
])

# Plotting
x = np.arange(len(averaged_data["Model"]))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, averaged_data["Exact Accuracy"], width, label="Exact Match Accuracy", color="#60a5fa")
bars2 = ax.bar(x + width/2, averaged_data["Partial Match Accuracy"], width, label="Partial Match Accuracy", color="#10b981")

# Add data labels
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height/2, f"{height:.2f}", ha='center', va='center', fontsize=10, color='white')

for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height/2, f"{height:.2f}", ha='center', va='center', fontsize=10, color='white')

# Labels and layout
ax.set_xticks(x)
ax.set_xticklabels(averaged_data["Model"], fontsize=11)
ax.set_ylabel("Accuracy", fontsize=12)
ax.set_title("🔬 Average Exact and Partial Match Accuracy by LLM", fontsize=14, weight='bold')
ax.set_ylim(0, 1.05)
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig("llm_average_accuracy_comparison.png")
plt.show()


import pandas as pd
from rapidfuzz import process, fuzz
import matplotlib.pyplot as plt
import numpy as np
'''
# Load the files
manual_df = pd.read_csv("manual_mapping2.csv")
gpt41_df = pd.read_csv("gpt41_mapping.csv")
gpt4o_df = pd.read_csv("gpt4o_mapping.csv")
sonnet_df = pd.read_csv("claude_sonnet_mapping.csv")
opus_df = pd.read_csv("claude_opus_mapping.csv")
# Prepare the results
results = []
correct_matches = []
incorrect_matches = []
# Loop through techniques
for tech in gpt41_df["Technique"].unique():
    gpt_sub = gpt41_df[gpt41_df["Technique"] == tech]

    total = 0
    correct = 0

    for _, gpt_row in gpt_sub.iterrows():
        gpt_complex = gpt_row["Complex Name"]
        gpt_org = gpt_row["Organism"]

        # Fuzzy match to manual complex names
        best_match, score, idx = process.extractOne(
            gpt_complex, manual_df["Complex Name"], scorer=fuzz.token_sort_ratio
        )

        if score >= 40:  # you can adjust this threshold
            manual_row = manual_df.iloc[idx]
            manual_org = manual_row["Organism"]

            total += 1
            match_record = {
                "GPT Organism": gpt_org,
                "Manual Organism": manual_org
            }
        if gpt_org == manual_org:
            correct += 1
            correct_matches.append(match_record)
        else:
            incorrect_matches.append(match_record)

    accuracy = correct / total if total else 0
    results.append({
        "Technique": tech,
        "Total (fuzzy matched)": total,
        "Correct Matches": correct,
        "Accuracy": round(accuracy, 2)
    })
correct_df = pd.DataFrame(correct_matches)
incorrect_df = pd.DataFrame(incorrect_matches)

# Show the result
accuracy_gpt41 = pd.DataFrame(results)
print("Accuracy results for gpt41: ", accuracy_gpt41)
'''

# Load datasets
manual_df = pd.read_csv("manual_mapping2.csv")
gpt41_df = pd.read_csv("gpt41_mapping.csv")
gpt4o_df = pd.read_csv("gpt4o_mapping.csv")
sonnet_df = pd.read_csv("claude_sonnet_mapping.csv")
opus_df = pd.read_csv("claude_opus_mapping.csv")

# Store results
all_results = []

models = {
    "gpt-4-1": gpt41_df,
    "gpt-4o": gpt4o_df,
    "claude-sonnet": sonnet_df,
    "claude-opus": opus_df,
}

# Accuracy calculation
for model_name, df in models.items():
    for tech in df["Technique"].unique():
        gpt_sub = df[df["Technique"] == tech]
        total = 0
        correct = 0

        for _, gpt_row in gpt_sub.iterrows():
            gpt_complex = gpt_row["Complex Name"]
            gpt_org = str(gpt_row["Organism"]).strip().lower()

            best_match, score, idx = process.extractOne(
                gpt_complex, manual_df["Complex Name"], scorer=fuzz.token_sort_ratio
            )

            if score >= 40:
                manual_row = manual_df.iloc[idx]
                manual_org = str(manual_row["Organism"]).strip().lower()
                total += 1
                if gpt_org == manual_org:
                    correct += 1

        accuracy = correct / total if total else 0
        all_results.append({
            "Model": model_name,
            "Technique": tech,
            "Accuracy": round(accuracy, 2)
        })

# Prepare plotting data
results_df = pd.DataFrame(all_results)

techniques = ["zero-shot", "few-shot", "contextual"]
bar_width = 0.2
x = np.arange(len(techniques))

# Plot GPT Models
fig, axs = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
fig.suptitle("Organism Prediction Accuracy by Technique", fontsize=16)

# GPT plot
gpt_models = ["gpt-4-1", "gpt-4o"]
colors_gpt = ["#a6cee3", "#1f78b4"]

for i, model in enumerate(gpt_models):
    y = [results_df[(results_df["Model"] == model) & (results_df["Technique"] == t)]["Accuracy"].values[0] for t in techniques]
    axs[0].bar(x + i * bar_width, y, bar_width, label=model, color=colors_gpt[i])

axs[0].set_title("GPT Models")
axs[0].set_ylabel("Organism Accuracy")
axs[0].set_xticks(x + bar_width / 2)
axs[0].set_xticklabels(techniques)
axs[0].legend()
axs[0].set_ylim(0, 1)

# Claude plot
claude_models = ["claude-sonnet", "claude-opus"]
colors_claude = ["#b2df8a", "#33a02c"]

for i, model in enumerate(claude_models):
    y = [results_df[(results_df["Model"] == model) & (results_df["Technique"] == t)]["Accuracy"].values[0] for t in techniques]
    axs[1].bar(x + i * bar_width, y, bar_width, label=model, color=colors_claude[i])

axs[1].set_title("Claude Models")
axs[1].set_xticks(x + bar_width / 2)
axs[1].set_xticklabels(techniques)
axs[1].legend()

plt.tight_layout()
plt.show()

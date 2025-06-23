import pandas as pd
from pathlib import Path

def compare_accessions_with_missing(manual_csv: str, pred_csv: str) -> pd.DataFrame:
    manual_df = pd.read_csv(manual_csv)
    pred_df = pd.read_csv(pred_csv)

    manual_df.columns = [c.strip() for c in manual_df.columns]
    pred_df.columns = [c.strip() for c in pred_df.columns]

    def split_tokens(cell):
        if pd.isna(cell) or str(cell).strip() == "":
            return []
        return [t.strip() for t in str(cell).split(";")]

    # ground‑truth lookup: complex -> (set of accessions, missing count)
    gt_lookup = {}
    gt_missing_lookup = {}
    for name, cell in zip(manual_df["Complex Name"], manual_df["Accession_Mapped"]):
        tokens = split_tokens(cell)
        missing = sum(1 for t in tokens if t == "" or t.upper() == "NOT FOUND")
        acc_set = {t.upper() for t in tokens if t and t.upper() != "NOT FOUND"}
        gt_lookup[name.strip().lower()] = acc_set
        gt_missing_lookup[name.strip().lower()] = missing

    # stats per technique
    stats = {}

    def ensure_row(tech):
        if tech not in stats:
            stats[tech] = {"TP":0,"FP":0,"FN":0,"TN":0,
                           "Missing_Pred":0,"Missing_GT":0}

    for _, row in pred_df.iterrows():
        tech = row["Technique"]
        ensure_row(tech)

        complex_name = str(row["Complex Name"]).strip().lower()
        gt_set = gt_lookup.get(complex_name, set())
        gt_missing = gt_missing_lookup.get(complex_name, 0)

        pred_tokens = split_tokens(row["Accession_Mapped"])
        missing_pred = sum(1 for t in pred_tokens if t == "" or t.upper() == "NOT FOUND")
        pred_set = {t.upper() for t in pred_tokens if t and t.upper() != "NOT FOUND"}

        stats[tech]["Missing_Pred"] += missing_pred
        stats[tech]["Missing_GT"] += gt_missing

        if not gt_set and not pred_set:
            stats[tech]["TN"] += 1
            continue

        stats[tech]["TP"] += len(pred_set & gt_set)
        stats[tech]["FP"] += len(pred_set - gt_set)
        stats[tech]["FN"] += len(gt_set - pred_set)

    # build dataframe
    summary = pd.DataFrame(stats).T

    # Accuracy for **each technique**
    denom = summary["TP"] + summary["FP"] + summary["FN"] + summary["TN"]
    summary["Accuracy"] = (summary["TP"] + summary["TN"]) / denom
    summary.loc[denom == 0, "Accuracy"] = pd.NA      # avoid 0-division NaN

    # Precision / Recall / F1
    summary["Precision"] = summary["TP"] / (summary["TP"] + summary["FP"])
    summary["Recall"]    = summary["TP"] / (summary["TP"] + summary["FN"])
    summary["F1-score"]  = 2 * summary["Precision"] * summary["Recall"] / (
                            summary["Precision"] + summary["Recall"])

    # ---------------- overall line -----------------
    overall = summary[["TP","FP","FN","TN","Missing_Pred","Missing_GT"]].sum()
    overall.name = "Overall"

    total = overall["TP"] + overall["FP"] + overall["FN"] + overall["TN"]
    overall["Accuracy"]  = (overall["TP"] + overall["TN"]) / total if total else pd.NA
    overall["Precision"] = overall["TP"] / (overall["TP"] + overall["FP"]) if overall["TP"]+overall["FP"] else pd.NA
    overall["Recall"]    = overall["TP"] / (overall["TP"] + overall["FN"]) if overall["TP"]+overall["FN"] else pd.NA
    if pd.notna(overall["Precision"]) and pd.notna(overall["Recall"]) and (overall["Precision"]+overall["Recall"]) != 0:
        overall["F1-score"] = 2*overall["Precision"]*overall["Recall"]/(
                              overall["Precision"]+overall["Recall"])
    else:
        overall["F1-score"] = pd.NA

    summary = pd.concat([summary, overall.to_frame().T])
    return summary.reset_index().rename(columns={"index": "Technique"})

results = compare_accessions_with_missing("manual_mapping2.csv", "claude_opus_mapping.csv")

print(results)

# …or save:
results.to_csv("gpt-4.1_evals.csv", index=False)
